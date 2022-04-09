from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
from copy import copy
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from pm4py.objects.petri_net.utils import petri_utils


class MyToken:
    def __init__(self):
        self.direct_ancestors = set()  # just ancestors
        self.red_ancestors = set()    # ancestors before bad transitions


def format_alignment(alignment):
    '''
    'log': labels
    'model': (label, name)
    '''
    log_steps = [labels[0] for names, labels in alignment]
    model_steps = [(labels[1], names[1]) for names, labels in alignment]
    data = {'log': log_steps, 'model': model_steps}
    return data


def __find_bad_pairs(net: PetriNet, alignment, initial_marking, final_marking):
    '''
    alignment for one trace
              (must be formatted)
    '''


    '''
    в alignment:
     - если 1-ый      - не sync move, то сделаем пару со start position
     - если последний - не sync move, то сделаем пару с end position
    '''
    bad_pairs = {}  # pair: cnt

    marking = {}  # place: [tokens]
    for plc in net.places:
        marking[plc] = []

    start_places = {place for place, cnt in initial_marking.items()}
    for place, cnt in initial_marking.items():
        marking[place] = [MyToken()] * cnt

    def add_bad_pair(pair):
        nonlocal bad_pairs
        if pair not in bad_pairs:
            bad_pairs[pair] = 1
        else:
            bad_pairs[pair] += 1

    for i in range(len(alignment['model'])):
        model_label, model_name = alignment['model'][i]
        log_label = alignment['log'][i]

        if model_label != '>>':  # fired transition
            # find transition
            fired_transition = petri_utils.get_transition_by_name(net, model_name)

            consumed_tokens = []
            # consume tokens
            for in_arc in fired_transition.in_arcs:
                in_plc = in_arc.source
                if not marking[in_plc]:
                    error = 0
                consumed_tokens.append(marking[in_plc].pop(0))

            # unite lists
            union_token = MyToken()
            for token in consumed_tokens:
                union_token.red_ancestors = set.union(union_token.red_ancestors,
                                                      token.red_ancestors)
                union_token.direct_ancestors = set.union(union_token.direct_ancestors,
                                                         token.direct_ancestors)

            if model_label is None:  # hidden transition
                # just save the condition
                pass
            elif model_label == log_label:  # sync move
                for red_ancestor in union_token.red_ancestors:  # add a pair of transitions
                    pair = (red_ancestor, fired_transition)
                    add_bad_pair(pair)
                union_token.red_ancestors = set()
                union_token.direct_ancestors = {fired_transition}
            elif log_label == '>>':  # model-only move
                union_token.red_ancestors = set.union(union_token.red_ancestors,
                                                      union_token.direct_ancestors)

            # produce tokens
            for out_arc in fired_transition.out_arcs:
                out_plc = out_arc.target
                marking[out_plc].append(copy(union_token))

        else:  # log-only move
            pass

    end_places = {place for place, cnt in final_marking.items()}
    for place, tokens in marking.items():
        for token in tokens:
            for red_anc in token.red_ancestors:
                for end in end_places:
                    add_bad_pair((red_anc, end))

    return bad_pairs


def find_bad_pairs(net: PetriNet, initial_marking, final_marking, aligned_traces):
    '''
    :param aligned_traces:
        the result of applying the alignments algo to the `log` and `net`
    :return
        dict with elements {(t1, t2): count},
        where (t1, t2) is a bad pair of transitions or start/end places
         and
        count is the number of its detections
    '''
    bad_pairs = {}

    for aligned_trace in aligned_traces:
        # print(aligned_trace)
        alignment = format_alignment(aligned_trace['alignment'])
        cur_bad_pairs = __find_bad_pairs(net, alignment, initial_marking, final_marking)
        for plc, cnt in cur_bad_pairs.items():
            if plc in bad_pairs:
                bad_pairs[plc] += cnt
            else:
                bad_pairs[plc] = cnt

    return bad_pairs
