from copy import copy

from pm4py.objects.petri_net.obj import PetriNet
from typing import Optional, Dict, Any, Set, Union
from hammocks_covering.obj import Hammock
from enum import Enum
from pm4py.util import exec_utils


class Parameters(Enum):
    PARAM_SOURCE_NODE_TYPE = 'source_node_type'
    PARAM_SINK_NODE_TYPE = 'sink_node_type'


class NodeTypes:
    PLACE_TYPE = (1 << 0)
    NOT_HIDDEN_TRANS_TYPE = (1 << 1)
    HIDDEN_TRANS_TYPE = (1 << 2)


class NodeFilter:
    def __init__(self, permitted_types=NodeTypes.PLACE_TYPE):
        permitted_types |= NodeTypes.PLACE_TYPE
        self.__permitted_types = permitted_types

    def is_permitted(self, obj: Union[PetriNet.Place, PetriNet.Transition]):
        if isinstance(obj, PetriNet.Place):
            return self.__permitted_types & NodeTypes.PLACE_TYPE
        else:
            if obj.label is None:  # hidden transition
                return self.__permitted_types & NodeTypes.HIDDEN_TRANS_TYPE
            else:
                return self.__permitted_types & NodeTypes.NOT_HIDDEN_TRANS_TYPE


def _bfs(start_nodes, target_node=None, stop_nodes=None, used=None, reverse_order: bool = False):
    parents = {}
    used = set() if used is None else used
    stop_nodes = set() if stop_nodes is None else stop_nodes
    cur_level = []
    for node in start_nodes:
        if target_node is not None:
            if node == target_node:
                return [node]
            parents[node] = None
        used.add(node)
        cur_level.append(node)

    next_level = []
    visited_stops = set()

    while cur_level:
        for node in cur_level:
            if node in stop_nodes:
                visited_stops.add(node)
                continue
            for arc in (node.in_arcs if reverse_order else node.out_arcs):
                next_node = (arc.source if reverse_order else arc.target)
                if next_node not in used:
                    if target_node is not None:
                        parents[next_node] = node
                        if node == target_node:
                            break
                    used.add(next_node)
                    next_level.append(next_node)
        cur_level = next_level
        next_level = []

    if target_node is not None:
        path = []
        cur_node = target_node
        if parents[target_node] is None:
            raise Exception("The target_node is not reachable from the given set of nodes")

        while cur_node is not None:
            path.append(cur_node)
            cur_node = parents[cur_node]
        path = list(reversed(path))
        return path
    else:
        return visited_stops


def _find_path(start_nodes, target_node, reverse_order=False):
    """
    Returns
    ---------------
    path
        The minimal path from one of the `start_nodes` to the `target_node`
    """
    return _bfs(start_nodes, target_node=target_node, reverse_order=reverse_order)


def _find_candidate(covered_nodes, target_node, reverse_order=False, cand_filter: NodeFilter = NodeFilter()):
    '''
    :return:
        returns the `target_node` if none of the candidates are permitted by the `cand_filter`
    '''
    path = _find_path(covered_nodes, target_node, reverse_order=reverse_order)
    pos_in_path = {node: pos for pos, node in enumerate(path)}

    middle_pos = 0
    suffix_nodes = set(path)
    used = set()

    def reduce_suffix_by(k):
        nonlocal middle_pos, suffix_nodes
        for _ in range(middle_pos, middle_pos + k):
            if middle_pos >= len(path):
                raise Exception("Path length exceeded")
            suffix_nodes.remove(path[middle_pos])
            middle_pos += 1

    prefix_node_pos = -1
    while True:
        while prefix_node_pos < middle_pos:
            start_nodes = covered_nodes if prefix_node_pos == -1 else [path[prefix_node_pos]]
            visited_suffix_nodes = _bfs(start_nodes, stop_nodes=suffix_nodes, used=used, reverse_order=reverse_order)

            new_middle_pos = middle_pos
            for node in visited_suffix_nodes:
                new_middle_pos = max(new_middle_pos, pos_in_path[node])
            if new_middle_pos > middle_pos:
                reduce_suffix_by(new_middle_pos - middle_pos)
            prefix_node_pos += 1

        if middle_pos + 1 == len(path) or cand_filter.is_permitted(path[middle_pos]):
            break
        reduce_suffix_by(1)

    return path[middle_pos]


def _find_source_candidate(covered_nodes, net_source, parameters=None):
    source_node_type = exec_utils.get_param_value(Parameters.PARAM_SOURCE_NODE_TYPE, parameters, NodeTypes.PLACE_TYPE)
    return _find_candidate(covered_nodes, net_source, reverse_order=True, cand_filter=NodeFilter(source_node_type))


def _find_sink_candidate(covered_nodes, net_sink, parameters=None):
    sink_node_type = exec_utils.get_param_value(Parameters.PARAM_SINK_NODE_TYPE, parameters, NodeTypes.PLACE_TYPE)
    return _find_candidate(covered_nodes, net_sink, cand_filter=NodeFilter(sink_node_type))


def _expand_as_hammock(covered_nodes, source_cand, sink_cand):
    new_nodes = set()
    for node in covered_nodes:
        if node != source_cand:
            for arc in node.in_arcs:
                new_nodes.add(arc.source)
        if node != sink_cand:
            for arc in node.out_arcs:
                new_nodes.add(arc.target)
    return new_nodes.difference(covered_nodes)


def apply(covered_nodes: Set[Union[PetriNet.Place, PetriNet.Transition]],
          net_source: PetriNet.Place, net_sink: PetriNet.Place,
          parameters: Optional[Dict[Any, Any]] = None):
    """
    Parameters
    ---------------
    net
        Petri net
    covered_nodes
        The set of nodes to cover
    net_source
        The source node of the net
    net_sink
        The sink node of the net
    parameters
        Parameters of the algorithm
    Returns
    ---------------
    hammock
        The minimal hammock that covers the `covered_nodes`
    """
    covered_nodes = set(covered_nodes)

    while True:
        source_cand = _find_source_candidate(covered_nodes, net_source, parameters)
        sink_cand = _find_sink_candidate(covered_nodes, net_sink, parameters)

        covered_nodes.add(source_cand)
        covered_nodes.add(sink_cand)
        new_nodes = _expand_as_hammock(covered_nodes, source_cand, sink_cand)
        if not new_nodes:
            break
        covered_nodes = covered_nodes.union(new_nodes)

    return Hammock(source_cand, sink_cand, covered_nodes)
