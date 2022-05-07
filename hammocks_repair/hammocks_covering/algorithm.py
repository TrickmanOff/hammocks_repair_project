from enum import Enum
from typing import Optional, Dict, Any, Union, Iterable, List, Tuple

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.util import exec_utils

from hammocks_repair.hammocks_covering.obj import Hammock
from hammocks_repair.hammocks_covering.variants import minimal_hammock
from hammocks_repair.hammocks_covering.variants.minimal_hammock import NodeTypes
from hammocks_repair.utils.pn_typing import NetNode


class Variants(Enum):
    """
    algorithms for searching the minimal hammock covering the given set of nodes
    """
    DEFAULT_ALGO = minimal_hammock


class Parameters(Enum):
    HAMMOCK_PERMITTED_SOURCE_NODE_TYPE = minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE.value
    HAMMOCK_PERMITTED_SINK_NODE_TYPE = minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE.value


DEFAULT_HAMMOCK_PERMITTED_SOURCE_NODE_TYPE = NodeTypes.PLACE_TYPE
DEFAULT_HAMMOCK_PERMITTED_SINK_NODE_TYPE = NodeTypes.PLACE_TYPE


def apply(net: PetriNet, covered_nodes: Union[Iterable[NetNode], Iterable[Tuple[NetNode, NetNode]]], as_graph=False, parameters: Optional[Dict[Any, Any]] = None, variant: Variants = Variants.DEFAULT_ALGO):
    """
    Find a set of hammocks covering the nodes present in the `linked_pairs` with each pair covered by one hammock

    Parameters
    ------------
    net
        a Petri net
    covered_nodes
        if as_graph=False: set of vertices to be covered by one hammock
        if as_graph=True: pairs of nodes that should be in one hammock (linked_pairs)
    as_graph
        determines how to interpret the `covered_nodes`
    parameters
        Parameters of the algorithm:
            Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE - permitted node type of the hammock's source (ORed NodeTypes), by default: DEFAULT_HAMMOCK_PERMITTED_SOURCE_NODE_TYPE
            Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE - permitted node type of the hammock's sink (ORed NodeTypes), by default: DEFAULT_HAMMOCK_PERMITTED_SINK_NODE_TYPE
    variant
        Variants of the algorithm, possible values:
            - Variants.DEFAULT_ALGO

    Returns
    ------------
    hammocks
        List of covering hammocks
    """
    if not check_soundness.check_wfnet(net):
        raise Exception("Trying to apply hammocks covering search on a Petri Net that is not a WF-net")

    net_source = check_soundness.check_source_place_presence(net)
    net_sink = check_soundness.check_sink_place_presence(net)

    if as_graph:
        return apply_to_graph(net_source, net_sink, covered_nodes, parameters, variant)
    else:
        return apply_to_set(net_source, net_sink, covered_nodes, parameters, variant)


def apply_to_set(net_source: PetriNet.Place, net_sink: PetriNet.Place, covered_nodes: Iterable[NetNode], parameters: Optional[Dict[Any, Any]] = None, variant: Variants = Variants.DEFAULT_ALGO):
    return exec_utils.get_variant(variant).apply(covered_nodes, net_source, net_sink, parameters)


def _get_component(graph, v):  # bfs
    cur_level = [v]
    used = {v}

    while cur_level:
        next_level = []
        for next_node in graph[v]:
            if next_node not in used:
                used.add(next_node)
                next_level.append(next_node)
        cur_level = next_level
    return used


def apply_to_graph(net_source: PetriNet.Place, net_sink: PetriNet.Place, linked_pairs: Iterable[Tuple[NetNode, NetNode]], parameters: Optional[Dict[Any, Any]] = None, variant: Variants = Variants.DEFAULT_ALGO) -> List[Hammock]:
    cr_graph = {}  # linked_pairs -> graph
    for u, v in linked_pairs:
        if u not in cr_graph:
            cr_graph[u] = set()
        cr_graph[u].add(v)
        if v not in cr_graph:
            cr_graph[v] = set()
        cr_graph[v].add(u)
    cr_graph_nodes = set(cr_graph.keys())

    hammocks = {}  # {node : covering hammock}
    for uncovered_node in cr_graph_nodes:
        if uncovered_node in hammocks:
            continue

        component = _get_component(cr_graph, uncovered_node)

        while True:
            cur_hammock = exec_utils.get_variant(variant).apply(component, net_source, net_sink, parameters)

            new_nodes = set()
            for node in cur_hammock.nodes:
                if node in component or node in new_nodes:
                    continue
                elif node in hammocks:  # intersection with another hammock
                    intersected_hammock = hammocks[node]
                    for other_node in intersected_hammock.nodes:
                        hammocks.pop(other_node)
                        new_nodes.add(other_node)
                elif node in cr_graph_nodes:  # intersection with an uncovered component
                    new_nodes.update(_get_component(cr_graph, node))

            if not new_nodes:
                break
            component = cur_hammock.nodes.union(new_nodes)

        for node in cur_hammock.nodes:
            hammocks[node] = cur_hammock

    return list(set(hammocks.values()))
