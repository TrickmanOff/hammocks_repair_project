from pm4py.objects.petri_net.obj import PetriNet

from hammocks_repair.conformance_analysis import bad_pairs_selection
from typing import Optional, Dict, Any
from hammocks_repair.hammocks_covering import algorithm as hammocks_covering
from hammocks_repair.hammocks_covering.algorithm import NodeTypes
from copy import deepcopy
from hammocks_repair.utils import net_helpers

# for discovering a subprocess
from hammocks_repair.hammocks_covering.obj import Hammock
from pm4py.objects.conversion.log import converter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.objects.petri_net.utils import petri_utils
import time

from enum import Enum
from pm4py.util import exec_utils

import hammocks_repair.net_repair.naive_log_only.algorithm as naive_log_only_algo


class Parameters(Enum):
    HAMMOCK_PERMITTED_SOURCE_NODE_TYPE = hammocks_covering.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE.value
    HAMMOCK_PERMITTED_SINK_NODE_TYPE = hammocks_covering.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE.value
    SUBPROCESS_MINER_ALGO = 'hammocks_replacement_subprocess_miner_algo'  # any algorithm
    SUBPROCESS_MINER_ALGO_VARIANT = 'hammocks_replacement_subprocess_miner_algo_variant'
    PREREPAIR_VARIANT = 'hammocks_replacement_prerepair_variant'  # from PrerepairVariants
    SUPRESS_LOGONLY_IN_ALIGNMENTS = 'hammocks_replacement_supress_logonly_in_alignments'  # True/False
    # use special cost function to find alignments before applying hammocks replacement


class PrerepairVariants(Enum):
    NAIVE_LOG_ONLY = naive_log_only_algo


DEFAULT_SUBPROCESS_MINER_ALGO = inductive_miner
DEFAULT_SUBPROCESS_MINER_ALGO_VARIANT = None
DEFAULT_PREREPAIR_VARIANT = PrerepairVariants.NAIVE_LOG_ONLY


def discover_subprocess(hammock: Hammock, log, parameters):
    '''
    :param hammock:
        A hammock to be replaced
    :param log:
    :return:
        net, net_source, net_sink
    '''

    df = converter.apply(log, variant=converter.Variants.TO_DATA_FRAME)
    hammock_activities_labels = {node.label for node in hammock.nodes if isinstance(node, PetriNet.Transition) and node.label is not None}
    # don't forget about empty subtraces
    filtered_df = df[df['concept:name'].isin(hammock_activities_labels)]

    is_empty_subtrace = df['case:concept:name'].nunique() > filtered_df['case:concept:name'].nunique()
    if len(filtered_df) == 0:  # what if filtered log.xes is empty?
        net = PetriNet()
        net_source = petri_utils.add_place(net)
        net_sink = petri_utils.add_place(net)
    else:
        miner_algo = exec_utils.get_param_value(Parameters.SUBPROCESS_MINER_ALGO, parameters, DEFAULT_SUBPROCESS_MINER_ALGO)
        miner_algo_variant = exec_utils.get_param_value(Parameters.SUBPROCESS_MINER_ALGO_VARIANT, parameters, DEFAULT_SUBPROCESS_MINER_ALGO_VARIANT)
        if miner_algo_variant is None:
            net, _, _ = miner_algo.apply(filtered_df, parameters=parameters)
        else:
            net, _, _ = miner_algo.apply(filtered_df, variant=miner_algo_variant, parameters=parameters)

        net_source = check_soundness.check_source_place_presence(net)
        net_sink = check_soundness.check_sink_place_presence(net)

    if is_empty_subtrace:
        hidden_trans = petri_utils.add_transition(net)
        petri_utils.add_arc_from_to(net_source, hidden_trans, net)
        petri_utils.add_arc_from_to(hidden_trans, net_sink, net)

    net_source.name = 'hammock_src_' + str(time.time())
    net_sink.name = 'hammock_sink_' + str(time.time())
    return net, net_source, net_sink


def find_bad_hammocks(net: PetriNet, initial_marking, final_marking, aligned_traces, parameters: Optional[Dict[Any, Any]] = None):
    '''
    :return:
        hammocks: set of hammocks covering
        bad_pairs: dict of found bad pairs
    '''
    bad_pairs_dict = bad_pairs_selection.apply(net, initial_marking, final_marking, aligned_traces)

    hammocks = hammocks_covering.apply(net, bad_pairs_dict.keys(), as_graph=True, parameters=parameters)
    return hammocks, bad_pairs_dict


def replace_hammock(net: PetriNet, initial_marking, final_marking, hammock: Hammock,
                    subprocess_net: PetriNet, subprocess_source, subprocess_sink):
    '''
    replaces the `hammock` with the `subprocess_net` in the `net`

    Note that collisions between the names of nodes in the subprocess net and the net with hammocks are possible, so
    don't forget to call enumerate_nodes_successively()
    '''

    if isinstance(hammock.source, PetriNet.Transition):
        if len(subprocess_source.out_arcs) == 1:
            for out_arc in subprocess_source.out_arcs:
                new_subprocess_source = out_arc.target
                break
            net_helpers.remove_node(subprocess_net, subprocess_source)
            subprocess_source = new_subprocess_source
        else:
            new_subprocess_source = petri_utils.add_transition(subprocess_net)
            petri_utils.add_arc_from_to(new_subprocess_source, subprocess_source, subprocess_net)
            subprocess_source = new_subprocess_source

    if isinstance(hammock.sink, PetriNet.Transition):
        if len(subprocess_sink.in_arcs) == 1:
            for in_arc in subprocess_sink.in_arcs:
                new_subprocess_sink = in_arc.source
                break
            net_helpers.remove_node(subprocess_net, subprocess_sink)
            subprocess_sink = new_subprocess_sink
        else:
            new_subprocess_sink = petri_utils.add_transition(subprocess_net)
            petri_utils.add_arc_from_to(subprocess_sink, new_subprocess_sink, subprocess_net)
            subprocess_sink = new_subprocess_sink

    # add nodes and arcs from the subprocess to the net
    for arc in subprocess_net.arcs:
        net.arcs.add(arc)
    for plc in subprocess_net.places:
        net.places.add(plc)
    for trans in subprocess_net.transitions:
        net.transitions.add(trans)

    # connect source and sink of the subprocess with the net
    for in_arc in hammock.source.in_arcs:
        petri_utils.add_arc_from_to(in_arc.source, subprocess_source, net)
    for out_arc in hammock.sink.out_arcs:
        petri_utils.add_arc_from_to(subprocess_sink, out_arc.target, net)

    # update the markings if needed
    for del_plc, new_plc in zip([hammock.source, hammock.sink], [subprocess_source, subprocess_sink]):
        if not isinstance(del_plc, PetriNet.Place):
            continue

        for marking in [initial_marking, final_marking]:
            if del_plc in marking:
                marking[new_plc] = marking[del_plc]
                del marking[del_plc]

    # delete all former nodes from the net
    for node in hammock.nodes:
        net_helpers.remove_node(net, node)

    return net, initial_marking, final_marking


def enumerate_nodes_successively(net):
    for i, place in enumerate(net.places):
        place.name = 'p_' + str(i + 1)
    for i, trans in enumerate(net.transitions):
        trans.name = 't_' + str(i + 1)

    return net


def use_custom_cost_function(net, alignments, parameters):
    '''
    Parameters.PARAM_SYNC_COST_FUNCTION ->
    mapping of each transition in the model to corresponding synchronous costs
    Parameters.PARAM_MODEL_COST_FUNCTION ->
    mapping of each transition in the model to corresponding model cost
    Parameters.PARAM_TRACE_COST_FUNCTION ->
    mapping of each index of the trace to a positive cost value
    '''
    model_cost_function = {}
    sync_cost_function = {}
    for trans in net.transitions:
        if trans.label is not None:
            model_cost_function[trans] = 100
            sync_cost_function[trans] = 0
        else:
            model_cost_function[trans] = 1
    max_trace_len = 0
    for alignment_info in alignments:
        max_trace_len = max(max_trace_len, len(alignment_info['alignment']))

    trace_cost_function = [10000] * max_trace_len
    parameters[alignments_algo.Parameters.PARAM_MODEL_COST_FUNCTION] = model_cost_function
    parameters[alignments_algo.Parameters.PARAM_SYNC_COST_FUNCTION] = sync_cost_function
    parameters[alignments_algo.Parameters.PARAM_TRACE_COST_FUNCTION] = trace_cost_function
    return parameters


def apply(net: PetriNet, initial_marking, final_marking, log, alignments=None, parameters: Optional[Dict[Any, Any]] = None):
    '''
    :param parameters:
        SUBPROCESS_MINER_ALGO - process discovery algorithm to use for discovering subprocesses
        default: inductive_miner

        parameters for the miner could be specified
    '''
    net, initial_marking, final_marking = net_helpers.deepcopy_net(net, initial_marking,
                                                                   final_marking)

    alignments_parameters = {
        alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
    }

    prerepair_algo = exec_utils.get_param_value(Parameters.PREREPAIR_VARIANT, parameters, DEFAULT_PREREPAIR_VARIANT)
    if prerepair_algo is not None:
        # applying prerepair
        if alignments is None:
            alignments = alignments_algo.apply_log(log, net, initial_marking, final_marking,
                                               parameters=alignments_parameters)
            prerepair_algo.apply(net, initial_marking, final_marking, log, alignments, parameters)

    should_recalculate_alignments = False
    if prerepair_algo is None:
        if alignments is None:
            should_recalculate_alignments = True
    else:
        if prerepair_algo == PrerepairVariants.NAIVE_LOG_ONLY.value:
            if parameters.get(naive_log_only_algo.Parameters.MODIFY_ALIGNMENTS_MODE, naive_log_only_algo.DEFAULT_MODIFY_ALIGNMENTS_MODE) is naive_log_only_algo.ModifyAlignments.NONE:
                should_recalculate_alignments = True
        # hardcode for each possible prerepair_variants (that's probably not the best solution)

    if should_recalculate_alignments:
        supress_logonly_in_alignments = exec_utils.get_param_value(Parameters.SUPRESS_LOGONLY_IN_ALIGNMENTS, parameters, True)
        if supress_logonly_in_alignments:
            parameters = use_custom_cost_function(net, alignments, parameters)
        alignments = alignments_algo.apply_log(log, net, initial_marking, final_marking, parameters=alignments_parameters)

    hammocks, _ = find_bad_hammocks(net, initial_marking, final_marking, alignments, parameters)

    for hammock in hammocks:
        subproc_net, subproc_src, subproc_sink = discover_subprocess(hammock, log, parameters)
        replace_hammock(net, initial_marking, final_marking, hammock, subproc_net, subproc_src, subproc_sink)
    enumerate_nodes_successively(net)

    return net, initial_marking, final_marking
