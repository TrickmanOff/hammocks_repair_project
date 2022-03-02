from pm4py.objects.petri_net.obj import PetriNet
from conformance_analysis import finding_bad_pairs
from hammocks_covering import algorithm as hammocks_covering
from typing import Optional, Dict, Any
from hammocks_covering.algorithm import Parameters, NodeTypes


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
