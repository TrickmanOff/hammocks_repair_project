from typing import Optional, Dict, Any
from copy import copy

from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.algo.conformance.tokenreplay.variants import token_replay
from pm4py.objects.petri_net.utils import petri_utils

from utils import net_helpers


def get_log_only_moves_locations(net: PetriNet, initial_marking, final_marking, alignments):
    log_only_moves_locations = {}

    for alignment_info in alignments:
        marking = copy(initial_marking)
        alignment = alignment_info['alignment']

        for names, labels in alignment:
            model_name = names[1]
            model_label = labels[1]
            log_label = labels[0]

            if model_label == '>>':  # log-only move
                if log_label not in log_only_moves_locations:
                    log_only_moves_locations[log_label] = set(marking.keys())
                else:
                    log_only_moves_locations[log_label] = log_only_moves_locations[log_label].intersection(set(marking.keys()))
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

    # final_marking_set = set(final_marking.keys())
    del_transitions = []
    for t_label in log_only_moves_locations.keys():
        # log_only_moves_locations[t_label] = log_only_moves_locations[t_label].difference(final_marking_set)
        if not log_only_moves_locations[t_label]:
            del_transitions.append(t_label)
    for t_label in del_transitions:
        del log_only_moves_locations[t_label]

    return log_only_moves_locations


def apply(net: PetriNet, initial_marking, final_marking, log, alignments, parameters: Optional[Dict[Any, Any]] = None):
    log_only_moves_locations = get_log_only_moves_locations(net, initial_marking, final_marking, alignments)
    for t_label, location in log_only_moves_locations.items():
        transition = net_helpers.get_transition_by_label(net, t_label)
        if transition is None:
            transition = petri_utils.add_transition(net, name=None, label=t_label)
        for plc in location:
            petri_utils.add_arc_from_to(plc, transition, net)
            petri_utils.add_arc_from_to(transition, plc, net)

    return net, initial_marking, final_marking
