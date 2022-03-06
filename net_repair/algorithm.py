from pm4py.objects.petri_net.obj import PetriNet
from conformance_analysis import finding_bad_pairs
from hammocks_covering import algorithm as hammocks_covering
from typing import Optional, Dict, Any
from hammocks_covering.algorithm import Parameters, NodeTypes
from copy import deepcopy
from utils import net_helpers

# for discovering a subprocess
from hammocks_covering.obj import Hammock
from pm4py.objects.conversion.log import converter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.objects.petri_net.utils import petri_utils
import time


def __conv_pairs_to_graph(pairs):
    '''
    converts given pairs to a graph for the hammocks covering algo
    '''
    graph = {}
    for a, b in pairs:
        if a not in graph:
            graph[a] = []
        graph[a].append(b)
        if b not in graph:
            graph[b] = []
        graph[b].append(a)
    return graph


def discover_subprocess(hammock: Hammock, log):
    '''
    :param hammock:
        A hammock to be replaces
    :param log:
    :return:
        net, net_source, net_sink
    '''

    df = converter.apply(log, variant=converter.Variants.TO_DATA_FRAME)
    hammock_activities_labels = {node.label for node in hammock.nodes if isinstance(node, PetriNet.Transition) and node.label is not None}
    # what if empty?
    filtered_df = df[df['concept:name'].isin(hammock_activities_labels)]
    net, _, _ = inductive_miner.apply(filtered_df)

    # if the hammock starts or ends with a transition
    # just add an artificial transition to a subprocess

    net_source = check_soundness.check_source_place_presence(net)
    if isinstance(hammock.source, PetriNet.Transition):
        hidden_trans_source = petri_utils.add_transition(net)
        petri_utils.add_arc_from_to(hidden_trans_source, net_source, net)
        net_source = hidden_trans_source

    net_sink = check_soundness.check_sink_place_presence(net)
    if isinstance(hammock.sink, PetriNet.Transition):
        hidden_trans_sink = petri_utils.add_transition(net)
        petri_utils.add_arc_from_to(net_sink, hidden_trans_sink, net)
        net_sink = hidden_trans_sink

    net_source.name = 'hammock_src_' + str(time.time())
    net_sink.name = 'hammock_sink_' + str(time.time())
    return net, net_source, net_sink


def find_bad_hammocks(net: PetriNet, initial_marking, final_marking, log, parameters: Optional[Dict[Any, Any]] = None, aligned_traces=None):
    '''
    :return:
        hammocks: set of hammocks covering
        bad_pairs: dict of found bad pairs
    '''
    bad_pairs = finding_bad_pairs.find_bad_pairs(net, initial_marking, final_marking, log, aligned_traces)
    bad_pairs_g = __conv_pairs_to_graph(bad_pairs)

    hammocks = hammocks_covering.apply(net, bad_pairs_g, as_graph=True, parameters=parameters)
    return hammocks, bad_pairs


# to utils
def __remove_node(net, obj):
    if isinstance(obj, PetriNet.Place):
        petri_utils.remove_place(net, obj)
    else:
        petri_utils.remove_transition(net, obj)


def replace_hammock(net: PetriNet, initial_marking, final_marking, hammock: Hammock, subprocess_net, subprocess_source, subprocess_sink):
    # add nodes and arcs from the subprocess
    for arc in subprocess_net.arcs:
        net.arcs.add(arc)
    for plc in subprocess_net.places:
        net.places.add(plc)
    for trans in subprocess_net.transitions:
        net.transitions.add(trans)

    # connect source and sink
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
        __remove_node(net, node)

    return net, initial_marking, final_marking


def apply(net: PetriNet, initial_marking, final_marking, log, parameters: Optional[Dict[Any, Any]] = None, aligned_traces=None):
    # in order not to change the initial net
    net, initial_marking, final_marking = net_helpers.deepcopy_net(net, initial_marking, final_marking)
    hammocks, _ = find_bad_hammocks(net, initial_marking, final_marking, log, parameters, aligned_traces)

    for hammock in hammocks:
        subproc_net, subproc_src, subproc_sink = discover_subprocess(hammock, log)
        replace_hammock(net, initial_marking, final_marking, hammock, subproc_net, subproc_src, subproc_sink)

    return net, initial_marking, final_marking
