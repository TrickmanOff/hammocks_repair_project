from typing import Optional, Dict, Any, Set, List, Tuple
from copy import copy

from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.algo.conformance.tokenreplay.variants import token_replay
from pm4py.objects.petri_net.utils import petri_utils

from utils import net_helpers


def get_log_only_moves_locations(net: PetriNet, initial_marking, final_marking, alignments) -> Dict[str, List[Tuple[Set, List]]]:
    '''
    :return:
    t_label -> [
      (location - set of places, corresponding log-only moves in the alignments),
      ...
    ]
    '''
    log_only_moves_markings = {}
    # t_label -> {
    #   marking: [ (alignment, move_index), ... ],
    #   ...
    # }
    for alignment_info in alignments:
        marking = copy(initial_marking)
        alignment = alignment_info['alignment']

        for move_index, move in enumerate(alignment):
            names, labels = move
            model_name = names[1]
            model_label = labels[1]
            log_label = labels[0]

            if model_label == '>>':  # log-only move
                if log_label not in log_only_moves_markings:
                    log_only_moves_markings[log_label] = {}
                marking_key = frozenset(marking)
                if marking_key not in log_only_moves_markings[log_label]:
                    log_only_moves_markings[log_label][marking_key] = []
                log_only_moves_markings[log_label][marking_key].append((alignment, move_index))
            else:  # fire the transition
                fired_transition = petri_utils.get_transition_by_name(net, model_name)
                for in_arc in fired_transition.in_arcs:
                    marking[in_arc.source] -= in_arc.weight
                    if marking[in_arc.source] == 0:
                        del marking[in_arc.source]
                for out_arc in fired_transition.out_arcs:
                    if out_arc.target not in marking:
                        marking[out_arc.target] = 0
                    marking[out_arc.target] += out_arc.weight

    log_only_moves_locations = {}  # t_label -> [ location1 - set of places, location2 - set of places, ... ]
    # finding intersections for locations
    for t_label, markings in log_only_moves_markings.items():
        alignments_moves = list(markings.values())
        markings = list(markings.keys())

        markings_for_plc = {}
        locations = []

        for i, marking in enumerate(markings):
            for plc in marking:
                if plc not in markings_for_plc:
                    markings_for_plc[plc] = set()
                markings_for_plc[plc].add(i)

        while True:
            max_markings_for_plc = set()
            for plc, plc_markings in markings_for_plc.items():
                if len(plc_markings) > len(max_markings_for_plc):
                    max_markings_for_plc = plc_markings
            max_markings_for_plc = copy(max_markings_for_plc)

            if not max_markings_for_plc:
                break

            cur_location = {plc for plc, plc_markings in markings_for_plc.items() if plc_markings == max_markings_for_plc}
            corresponding_alignments_moves = []
            for marking_index in max_markings_for_plc:
                corresponding_alignments_moves += alignments_moves[marking_index]
            locations.append((cur_location, corresponding_alignments_moves))

            for marking_index in max_markings_for_plc:
                for plc in markings[marking_index]:
                    markings_for_plc[plc].remove(marking_index)

        log_only_moves_locations[t_label] = locations

    return log_only_moves_locations


# changes the alignments
def apply(net: PetriNet, initial_marking, final_marking, log, alignments, parameters: Optional[Dict[Any, Any]] = None):
    log_only_moves_locations = get_log_only_moves_locations(net, initial_marking, final_marking, alignments)

    for t_label, locations_with_alignments_moves in log_only_moves_locations.items():
        for location, alignments_moves in locations_with_alignments_moves:
            transition = petri_utils.add_transition(net, name=None, label=t_label)
            for plc in location:
                petri_utils.add_arc_from_to(plc, transition, net)
                petri_utils.add_arc_from_to(transition, plc, net)
            for alignment, move_index in alignments_moves:
                names, labels = alignment[move_index]
                alignment[move_index] = ((names[0], transition.name), (labels[0], t_label))  # labels[0] == t_label

    for st_plc in list(initial_marking.keys()):
        if st_plc.in_arcs:
            new_st_plc = petri_utils.add_place(net)
            removed_arcs = []
            for in_arc in st_plc.in_arcs:
                trans = in_arc.source
                out_arc = net_helpers.find_arc(st_plc.name, trans.name, net)
                removed_arcs.append(out_arc)
                petri_utils.add_arc_from_to(new_st_plc, trans, net)
            for arc in removed_arcs:
                petri_utils.remove_arc(net, arc)

            hidden_trans = petri_utils.add_transition(net)
            petri_utils.add_arc_from_to(new_st_plc, hidden_trans, net)
            petri_utils.add_arc_from_to(hidden_trans, st_plc, net)

            initial_marking[new_st_plc] = initial_marking[st_plc]
            del initial_marking[st_plc]

    for end_plc in list(final_marking.keys()):
        if end_plc.out_arcs:
            new_end_plc = petri_utils.add_place(net)
            removed_arcs = []
            for out_arc in end_plc.out_arcs:
                trans = out_arc.target
                in_arc = net_helpers.find_arc(trans.name, end_plc.name, net)
                removed_arcs.append(in_arc)
                petri_utils.add_arc_from_to(trans, new_end_plc, net)
            for arc in removed_arcs:
                petri_utils.remove_arc(net, arc)

            hidden_trans = petri_utils.add_transition(net)
            petri_utils.add_arc_from_to(end_plc, hidden_trans, net)
            petri_utils.add_arc_from_to(hidden_trans, new_end_plc, net)

            final_marking[new_end_plc] = final_marking[end_plc]
            del final_marking[end_plc]

    return net, initial_marking, final_marking
