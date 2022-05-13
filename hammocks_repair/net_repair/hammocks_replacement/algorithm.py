import pandas as pd

from enum import Enum
from typing import Optional, Dict, Any, Tuple, Union
import time

from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import check_soundness, petri_utils
from pm4py.util import exec_utils, xes_constants, typing, constants as pm4_constants

from hammocks_repair.conformance_analysis import bad_pairs_selection
from hammocks_repair.hammocks_covering import algorithm as hammocks_covering
from utils import net_helpers
import hammocks_repair.net_repair.naive_log_only.algorithm as naive_log_only_algo

Hammock = hammocks_covering.Hammock
NodeTypes = hammocks_covering.NodeTypes


class Parameters(Enum):
    HAMMOCK_PERMITTED_SOURCE_NODE_TYPE = hammocks_covering.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE.value
    HAMMOCK_PERMITTED_SINK_NODE_TYPE = hammocks_covering.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE.value
    SUBPROCESS_MINER_ALGO = 'hammocks_replacement_subprocess_miner_algo'  # any algorithm
    SUBPROCESS_MINER_ALGO_VARIANT = 'hammocks_replacement_subprocess_miner_algo_variant'
    PREREPAIR_VARIANT = 'hammocks_replacement_prerepair_variant'  # from PrerepairVariants

    LOG_ACTIVITY_KEY = pm4_constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    LOG_CASE_KEY = pm4_constants.PARAMETER_CONSTANT_CASEID_KEY


class PrerepairVariants(Enum):
    NAIVE_LOG_ONLY = naive_log_only_algo


DEFAULT_SUBPROCESS_MINER_ALGO = inductive_miner
DEFAULT_SUBPROCESS_MINER_ALGO_VARIANT = inductive_miner.DEFAULT_VARIANT_LOG
DEFAULT_PREREPAIR_VARIANT = PrerepairVariants.NAIVE_LOG_ONLY
DEFAULT_LOG_ACTIVITY_KEY = xes_constants.DEFAULT_NAME_KEY
DEFAULT_LOG_CASE_KEY = pm4_constants.CASE_CONCEPT_NAME


def discover_subprocess(hammock: Hammock, log: Union[pd.DataFrame, EventLog, EventStream], parameters: Optional[Dict[Any, Any]] = None) -> Tuple[PetriNet, PetriNet.Place, PetriNet.Place]:
    """
    Discover a subprocess on activities included in the hammock (which is potentially replaced), based on the log

    Parameters
    ------------
    hammock
        A hammock to be replaced
    parameters
        Parameters of the algorithm:
            Parameters.SUBPROCESS_MINER_ALGO - A process discovery algorithm to be used for discovering a subprocess (apply() method is used)
            Parameters.SUBPROCESS_MINER_ALGO_VARIANT - A variant of the process discovery algorithm to be used
            Parameters.LOG_ACTIVITY_KEY - The name of the attribute to be used as activity for process discovery
            Parameters.LOG_CASE_KEY - The name of the attribute to be used as case identifier

    Returns
    ------------
        net, net_source, net_sink - discovered net with source and sink nodes
    """

    log_activity_key = exec_utils.get_param_value(Parameters.LOG_ACTIVITY_KEY, parameters, DEFAULT_LOG_ACTIVITY_KEY)
    log_case_key = exec_utils.get_param_value(Parameters.LOG_CASE_KEY, parameters, DEFAULT_LOG_CASE_KEY)

    df = log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME)
    hammock_activities_labels = {node.label for node in hammock.nodes if isinstance(node, PetriNet.Transition) and node.label is not None}
    filtered_df = df[df[log_activity_key].isin(hammock_activities_labels)]

    # don't forget about empty subtraces
    is_empty_subtrace = df[log_case_key].nunique() > filtered_df[log_case_key].nunique()
    if len(filtered_df) == 0:  # what if filtered log is empty
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

    if is_empty_subtrace:  # don't forget about empty subtraces
        hidden_trans = petri_utils.add_transition(net)
        petri_utils.add_arc_from_to(net_source, hidden_trans, net)
        petri_utils.add_arc_from_to(hidden_trans, net_sink, net)

    net_source.name = 'hammock_src_' + str(time.time())
    net_sink.name = 'hammock_sink_' + str(time.time())
    return net, net_source, net_sink


def replace_hammock(net: PetriNet, initial_marking: Marking, final_marking: Marking, hammock: Hammock,
                    subprocess_net: PetriNet, subprocess_source: PetriNet.Place, subprocess_sink: PetriNet.Place) -> Tuple[PetriNet, Marking, Marking]:
    """
    Replace the `hammock` with the `subprocess_net` in the `net`

    Note that collisions between the names of nodes in the subprocess net and the net with hammocks are possible, so
    don't forget to change them,
    for example, via net_helpers.enumerate_nodes_successively()

    the given `net` is modified

    Parameters
    ------------
    net, initial_marking, final_marking
        Initial WF-net
    hammock
        A hammock to be replaced
    subprocess_net, subprocess_source, subprocess_sink
        A subprocess WF-net to replace the hammock

    Returns
    ------------
    net, initial_marking, final_marking
        Modified net with replaced hammock
    """

    if isinstance(hammock.source, PetriNet.Transition):
        if len(subprocess_source.out_arcs) == 1:
            new_subprocess_source = next(iter(subprocess_source.out_arcs)).target
            net_helpers.remove_node(subprocess_net, subprocess_source)
            subprocess_source = new_subprocess_source
        else:
            new_subprocess_source = petri_utils.add_transition(subprocess_net)
            petri_utils.add_arc_from_to(new_subprocess_source, subprocess_source, subprocess_net)
            subprocess_source = new_subprocess_source

    if isinstance(hammock.sink, PetriNet.Transition):
        if len(subprocess_sink.in_arcs) == 1:
            new_subprocess_sink = next(iter(subprocess_sink.in_arcs)).source
            net_helpers.remove_node(subprocess_net, subprocess_sink)
            subprocess_sink = new_subprocess_sink
        else:
            new_subprocess_sink = petri_utils.add_transition(subprocess_net)
            petri_utils.add_arc_from_to(subprocess_sink, new_subprocess_sink, subprocess_net)
            subprocess_sink = new_subprocess_sink

    # add nodes and arcs from the subprocess to the net
    net.arcs.update(subprocess_net.arcs)
    net.places.update(subprocess_net.places)
    net.transitions.update(subprocess_net.transitions)

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


def apply(net: PetriNet, initial_marking: Marking, final_marking: Marking,
          log: Union[pd.DataFrame, EventLog, EventStream], alignments: Union[typing.AlignmentResult, typing.ListAlignments]=None,
          parameters: Optional[Dict[Any, Any]] = None) -> Tuple[PetriNet, Marking, Marking]:
    """
    Apply hammocks replacement repair algorithm to the given `net` w.r.t the `log`

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
        Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE -> Permitted node type of the hammock's source (mask of ORed NodeTypes), by default: hammocks_covering.DEFAULT_HAMMOCK_PERMITTED_SOURCE_NODE_TYPE
        Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE -> Permitted node type of the hammock's sink (mask of ORed NodeTypes), by default: hammocks_covering.DEFAULT_HAMMOCK_PERMITTED_SINK_NODE_TYPE
        Parameters.SUBPROCESS_MINER_ALGO -> A process discovery algorithm to be used for discovering a subprocess (apply() method is used)
        Parameters.SUBPROCESS_MINER_ALGO_VARIANT -> A variant of the process discovery algorithm to be used
        Parameters.PREREPAIR_VARIANT -> An algorithm from PrerepairVariants to be used before applying hammocks replacement, None if no prerepair should be used
        Parameters.LOG_ACTIVITY_KEY -> The name of the attribute to be used as activity for process discovery
        Parameters.LOG_CASE_KEY -> The name of the attribute to be used as case identifier

        parameters for the miner could also be specified

    Returns
    ------------
    net, initial_marking, final_marking
        The repaired net
    """
    if not check_soundness.check_wfnet(net):
        raise Exception("Trying to apply hammocks replacement repair on a Petri Net that is not a WF-net")

    net, initial_marking, final_marking = net_helpers.deepcopy_net(net, initial_marking, final_marking)

    alignments_parameters = {
        alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
    }

    prerepair_algo = exec_utils.get_param_value(Parameters.PREREPAIR_VARIANT, parameters, DEFAULT_PREREPAIR_VARIANT)
    if prerepair_algo is not None:
        # applying prerepair
        if alignments is None:
            alignments = alignments_algo.apply_log(log, net, initial_marking, final_marking, parameters=alignments_parameters)
        net, initial_marking, final_marking = prerepair_algo.apply(net, initial_marking, final_marking, log, alignments, parameters)

        # hardcode for each possible prerepair_variants (that's probably not the best solution)
        if prerepair_algo == PrerepairVariants.NAIVE_LOG_ONLY.value:
            if parameters.get(naive_log_only_algo.Parameters.ALIGNMENTS_MODIFICATION_MODE, naive_log_only_algo.DEFAULT_MODIFY_ALIGNMENTS_MODE) == naive_log_only_algo.AlignmentsModificationMode.NONE:
                alignments = None

    if alignments is None:
        alignments = alignments_algo.apply_log(log, net, initial_marking, final_marking, parameters=alignments_parameters)

    bad_pairs = bad_pairs_selection.apply(net, initial_marking, final_marking, alignments)
    hammocks = hammocks_covering.apply(net, bad_pairs, as_pairs=True, parameters=parameters)

    for hammock in hammocks:
        subproc_net, subproc_src, subproc_sink = discover_subprocess(hammock, log, parameters)
        net, initial_marking, final_marking = replace_hammock(net, initial_marking, final_marking, hammock, subproc_net, subproc_src, subproc_sink)
    net_helpers.enumerate_nodes_successively(net)

    return net, initial_marking, final_marking
