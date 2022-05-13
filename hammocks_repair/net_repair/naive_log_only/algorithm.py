from copy import copy
from enum import Enum
from typing import Optional, Dict, Any, Set, List, Tuple, Union
import pandas as pd

from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils, check_soundness

from utils import net_helpers


class Parameters(Enum):
    ALIGNMENTS_MODIFICATION_MODE = 'modify_alignments_mode'  # from ModifyAlignments


class AlignmentsModificationMode(Enum):
    NONE = 'none'               # no modifications
    LOG2SYNC = 'sync'           # replace log-only moves with corresponding sync moves
    LOG2MODEL = 'model_only'    # replace log-only moves with corresponding model-only moves


DEFAULT_MODIFY_ALIGNMENTS_MODE = AlignmentsModificationMode.NONE


def _get_log_only_moves_insertion_places(net: PetriNet, initial_marking, alignments) -> Dict[str, List[Tuple[Set, List]]]:
    """
    Returns
    ------------
    places_sets_for_log_only_moves
        for each log-only move (t_label, >>) in the alignments:

        t_label -> [
          ( set of places, corresponding log-only moves in the alignments as pairs (alignment, move_index) ),
          ...,
        ]
    """
    log_only_moves_locations = {}
    # t_label -> {
    #   location_1 (frozenset): [ (alignment, move_index), ... ],
    #   ...
    #   location_q (frozenset): [ (alignment, move_index), ... ],
    # }
    for alignment_info in alignments:
        alignment = alignment_info['alignment']
        marking = copy(initial_marking)

        for move_index, move in enumerate(alignment):
            # ( (log_name, model_name), (log_label, model_label) )
            (_, model_name), (log_label, model_label) = move

            if model_label == '>>':  # log-only move
                if log_label not in log_only_moves_locations:
                    log_only_moves_locations[log_label] = {}
                location = frozenset(marking.keys())
                if location not in log_only_moves_locations[log_label]:
                    log_only_moves_locations[log_label][location] = []
                log_only_moves_locations[log_label][location].append((alignment, move_index))
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

    places_sets_for_log_only_moves = {}  # t_label -> [ (set of places, list of moves in the alignments), ...,  ]
    # finding intersections for locations
    for t_label, locations_dict in log_only_moves_locations.items():
        locations = list(locations_dict.keys())
        alignments_moves = list(locations_dict.values())

        locations_containing_place = {}  # place -> {location indices in `locations`}

        for i, location in enumerate(locations):
            for plc in location:
                if plc not in locations_containing_place:
                    locations_containing_place[plc] = set()
                locations_containing_place[plc].add(i)

        places_sets = []  # ( {p1, ..., } - places, [(alignment, move_index), ..., ] - alignments moves )

        while True:
            max_locations_for_plc = set()  # place with maximal number of locations containing it
            for plc, plc_locations in locations_containing_place.items():
                if len(plc_locations) > len(max_locations_for_plc):
                    max_locations_for_plc = plc_locations

            if not max_locations_for_plc:
                break

            # intersection of locations from `max_locations_for_plc`
            locations_intersection = set()
            for i in max_locations_for_plc:
                if not locations_intersection:
                    locations_intersection = set(locations[i])
                else:
                    locations_intersection.intersection_update(locations[i])

            corresponding_alignments_moves = []
            for location_index in max_locations_for_plc:
                corresponding_alignments_moves += alignments_moves[location_index]
            places_sets.append((locations_intersection, corresponding_alignments_moves))

            for location_index in copy(max_locations_for_plc):
                for plc in locations[location_index]:
                    locations_containing_place[plc].remove(location_index)

        places_sets_for_log_only_moves[t_label] = places_sets

    return places_sets_for_log_only_moves


def apply(net: PetriNet, initial_marking: Marking, final_marking: Marking,
          log: Union[pd.DataFrame, EventLog, EventStream], alignments=None, parameters: Optional[Dict[Any, Any]] = None) -> Tuple[PetriNet, Marking, Marking]:
    """
    Parameters
    ------------
    net, initial_marking, final_marking
        A WF-net to be repaired
    log
        Event log for the net repair
    alignments
        Optional alignments to be used in the algorithm.
        A parameter PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE should be set to True during their calculation.
        if not provided, they will be calculated
    parameters
        Parameters.ALIGNMENTS_MODIFICATION_MODE -> One of AlignmentsModificationMode: mode of alignments' modification during the repair

    Returns
    ------------
    net, initial_marking, final_marking
        The repaired net
    """
    if not check_soundness.check_wfnet(net):
        raise Exception("Trying to apply repair algorithm on a Petri Net that is not a WF-net")

    net, initial_marking, final_marking = net_helpers.deepcopy_net(net, initial_marking, final_marking)

    if alignments is None:
        alignments_parameters = {
            alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
        }
        alignments = alignments_algo.apply_log(log, net, initial_marking, final_marking, parameters=alignments_parameters)

    places_sets_for_log_only_moves = _get_log_only_moves_insertion_places(net, initial_marking, alignments)

    replace_logonly_mode = parameters.get(Parameters.ALIGNMENTS_MODIFICATION_MODE, DEFAULT_MODIFY_ALIGNMENTS_MODE)

    for t_label, places_sets_with_alignments_moves in places_sets_for_log_only_moves.items():
        for places_set, alignments_moves in places_sets_with_alignments_moves:
            transition = petri_utils.add_transition(net, name=None, label=t_label)
            for plc in places_set:
                petri_utils.add_arc_from_to(plc, transition, net)
                petri_utils.add_arc_from_to(transition, plc, net)
            for alignment, move_index in alignments_moves:
                # a move in alignment: ( (log_name, model_name), (log_label, model_label) )
                names, labels = alignment[move_index]
                if replace_logonly_mode == AlignmentsModificationMode.NONE:
                    continue
                elif replace_logonly_mode == AlignmentsModificationMode.LOG2SYNC:
                    alignment[move_index] = ((names[0], transition.name), (labels[0], t_label))  # labels[0] == t_label
                elif replace_logonly_mode == AlignmentsModificationMode.LOG2MODEL:
                    alignment[move_index] = ((None, transition.name), ('>>', t_label))

    # duplicating the start/end positions if some new transitions were added to them
    for st_plc in list(initial_marking.keys()):
        if st_plc.in_arcs:
            new_st_plc = petri_utils.add_place(net)

            hidden_trans = petri_utils.add_transition(net)
            petri_utils.add_arc_from_to(new_st_plc, hidden_trans, net)
            petri_utils.add_arc_from_to(hidden_trans, st_plc, net)

            for alignment_info in alignments:
                alignment = alignment_info['alignment']
                (_, model_name) = alignment[0][0]

                if model_name != hidden_trans.name:
                    alignment.insert(0, ((None, hidden_trans.name), ('>>', None)))

            initial_marking[new_st_plc] = initial_marking[st_plc]
            del initial_marking[st_plc]

    for end_plc in list(final_marking.keys()):
        if end_plc.out_arcs:
            new_end_plc = petri_utils.add_place(net)

            hidden_trans = petri_utils.add_transition(net)
            petri_utils.add_arc_from_to(end_plc, hidden_trans, net)
            petri_utils.add_arc_from_to(hidden_trans, new_end_plc, net)

            for alignment_info in alignments:
                alignment = alignment_info['alignment']
                (_, model_name) = alignment[-1][0]

                if model_name != hidden_trans.name:
                    alignment.append(((None, hidden_trans.name), ('>>', None)))

            final_marking[new_end_plc] = final_marking[end_plc]
            del final_marking[end_plc]

    return net, initial_marking, final_marking
