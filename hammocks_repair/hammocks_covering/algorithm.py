from enum import Enum

from hammocks_repair.hammocks_covering.obj import Hammock
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.util import exec_utils
from hammocks_repair.hammocks_covering.variants import minimal_hammock
from typing import Optional, Dict, Any, Union, Set
from pm4py.objects.petri_net.utils import check_soundness
from hammocks_repair.hammocks_covering.variants.minimal_hammock import NodeTypes


class Variants(Enum):
    DEFAULT_ALGO = minimal_hammock


class Parameters(Enum):
    HAMMOCK_PERMITTED_SOURCE_NODE_TYPE = minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE.value
    HAMMOCK_PERMITTED_SINK_NODE_TYPE = minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE.value


def apply(net: PetriNet, covered_nodes, as_graph=False, parameters: Optional[Dict[Any, Any]] = None, variant: Variants = Variants.DEFAULT_ALGO):
    # разделение на covered_nodes граф или просто мн-во вершин
    if not check_soundness.check_wfnet(net):
        raise Exception("Trying to apply hammocks covering search on a Petri Net that is not a WF-net")

    net_source = check_soundness.check_source_place_presence(net)
    net_sink = check_soundness.check_sink_place_presence(net)

    if as_graph:
        return apply_to_graph(net_source, net_sink, covered_nodes, parameters, variant)
    else:
        return apply_to_set(net_source, net_sink, covered_nodes, parameters, variant)


def apply_to_set(net_source, net_sink, covered_nodes, parameters: Parameters = None, variant: Variants = Variants.DEFAULT_ALGO):
    return exec_utils.get_variant(variant).apply(covered_nodes, net_source, net_sink, parameters)


def __bfs(graph, v, used: Set):
    cur_level = [v]
    used.add(v)

    while cur_level:
        next_level = []
        for next_node in graph[v]:
            if next_node not in used:
                used.add(next_node)
                next_level.append(next_node)
        cur_level = next_level


def apply_to_graph(net_source, net_sink, cr_graph: Dict, parameters: Parameters = None, variant: Variants = Variants.DEFAULT_ALGO):
    '''
    :param net_source:
    :param net_sink:
    :param cr_graph:
        covering relation graph, must be undirected
        cr_graph[`node`] - nodes that should be in the same hammock as the `node`
    :param parameters:
    :param variant:
    :return:
    '''
    hammocks = {}
    for uncovered_node in cr_graph.keys():
        if uncovered_node in hammocks:
            continue
        component = set()
        __bfs(cr_graph, uncovered_node, component)

        cur_hammock = exec_utils.get_variant(variant).apply(component, net_source, net_sink, parameters)
        component = cur_hammock.nodes

        while True:
            nodes_from_other_hammocks = set()
            for node in component:
                if node in hammocks:
                    # merge
                    intersected_hammock = hammocks[node]
                    for other_node in intersected_hammock.nodes:
                        hammocks.pop(other_node)
                        nodes_from_other_hammocks.add(other_node)

            if not nodes_from_other_hammocks:
                break
            component = component.union(nodes_from_other_hammocks)
            cur_hammock = exec_utils.get_variant(variant).apply(component, net_source, net_sink, parameters)
            component = cur_hammock.nodes

        for node in component:
            hammocks[node] = cur_hammock

    return set(hammocks.values())
