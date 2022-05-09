from typing import Union, Dict, Tuple, Sequence
from copy import copy

from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.util import typing

from hammocks_repair.utils.pn_typing import NetNode


# TODO: move to utils?
def format_alignment(alignment: Sequence[Tuple[Tuple[str, str], Tuple[str, str]]]) -> Dict[str, Sequence[Union[str, Tuple[str, str]]]]:
    """
    Convert the alignment to dict (for convenience of further use)

    Parameters
    ------------
    alignment
        sequence of tuples ( (log_name, model_name), (log_label, model_label) )

    Returns
    ------------
    formatted_alignment
        {
            'log': labels
            'model': (label, name)
        }
    """
    log_labels = [labels[0] for names, labels in alignment]
    model_nodes = [(labels[1], names[1]) for names, labels in alignment]
    formatted_alignment = {'log': log_labels, 'model': model_nodes}
    return formatted_alignment


def _select_bad_pairs(net: PetriNet, alignment, initial_marking, final_marking):
    """
    Parameters
    ------------
    alignment
        one aligned trace, must be formatted via format_alignment()
    """
    class MyToken:
        def __init__(self):
            self.green_ancestors = set()
            self.red_ancestors = set()

    bad_pairs = {}  # pair: cnt

    marking = {}  # place: [tokens]
    for place in net.places:
        marking[place] = []
    init_token = MyToken()
    init_token.green_ancestors = {*initial_marking.keys()}
    for place, cnt in initial_marking.items():
        marking[place] = [copy(init_token) for _ in range(cnt)]

    def add_bad_pair(bad_pairs, new_pair):
        if new_pair not in bad_pairs:
            bad_pairs[new_pair] = 1
        else:
            bad_pairs[new_pair] += 1

    for log_label, (model_label, model_name) in zip(alignment['log'], alignment['model']):
        if model_label == '>>':  # log-only move
            continue

        fired_transition = petri_utils.get_transition_by_name(net, model_name)
        if fired_transition is None:
            raise RuntimeError(f"No transition with name {model_name}: incorrect alignments")

        consumed_tokens = []
        # consume tokens
        for in_plc in [in_arc.source for in_arc in fired_transition.in_arcs]:
            consumed_tokens.append(marking[in_plc].pop(0))

        # unite sets
        united_green = set()
        united_red = set()
        for token in consumed_tokens:
            united_green.update(token.green_ancestors)
            united_red.update(token.red_ancestors)

        prod_token = MyToken()

        if log_label == '>>':  # model-only move
            if model_label is None:  # hidden transition
                prod_token.green_ancestors = united_green
                prod_token.red_ancestors = united_red
            else:
                prod_token.green_ancestors = set()
                prod_token.red_ancestors = united_green.union(united_red)
        else:  # sync move
            for red_ancestor in united_red:  # add a bad pair
                add_bad_pair(bad_pairs, (red_ancestor, fired_transition))
            prod_token.green_ancestors = {fired_transition}
            prod_token.red_ancestors = set()

        # produce tokens
        for out_plc in [out_arc.target for out_arc in fired_transition.out_arcs]:
            marking[out_plc].append(copy(prod_token))

    end_places = {place for place, cnt in final_marking.items()}
    for tokens_list in marking.values():
        for token in tokens_list:
            for red_anc in token.red_ancestors:
                for end_plc in end_places:
                    add_bad_pair(bad_pairs, (red_anc, end_plc))

    return bad_pairs


def apply(net: PetriNet, initial_marking: Marking, final_marking: Marking, aligned_traces: Union[typing.AlignmentResult, typing.ListAlignments]) -> Dict[Tuple[NetNode, NetNode], int]:
    """
    Select "bad" pairs of nodes (transitions or start/end places) based on the given alignments

    Parameters
    ------------
    aligned_traces
        a result of applying the alignments algo to some log and the `net`
        format of each aligned trace:
        {
            'alignment': sequence of tuples
                ( (log_name, model_name), (log_label, model_label) )
        }
        for this format a parameter PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE should be set to True
        when calculating alignments

    Returns
    ------------
    bad_pairs
        dict with elements {(t1, t2): count},
        where (t1, t2) is a bad pair of transitions or start/end places
         and
        count is the number of its detections
    """
    bad_pairs = {}

    for aligned_trace in aligned_traces:
        alignment = format_alignment(aligned_trace['alignment'])
        cur_bad_pairs = _select_bad_pairs(net, alignment, initial_marking, final_marking)
        for plc, cnt in cur_bad_pairs.items():
            if plc in bad_pairs:
                bad_pairs[plc] += cnt
            else:
                bad_pairs[plc] = cnt

    return bad_pairs
