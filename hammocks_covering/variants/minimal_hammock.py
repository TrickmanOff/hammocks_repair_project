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
    """
    if target_node is not None -> path mode
    otherwise                  -> traversal mode
    :return:
        in path mode
            a path from any of the start_nodes to the target_node
        in traversal mode
            new_used_nodes - set of the new nodes that became used during this traversal
            visited_stops
    """
    parents = {}
    used = set() if used is None else used
    stop_nodes = set() if stop_nodes is None else stop_nodes
    cur_level = []

    new_used_nodes = set()
    visited_stops = set()

    for node in start_nodes:
        if target_node is not None:
            if node == target_node:
                return [node]
            parents[node] = None
        if node in used:
            continue
        new_used_nodes.add(node)
        used.add(node)
        if node in stop_nodes:
            visited_stops.add(node)
            continue
        cur_level.append(node)

    next_level = []

    while cur_level:
        for node in cur_level:
            for arc in (node.in_arcs if reverse_order else node.out_arcs):
                next_node = (arc.source if reverse_order else arc.target)
                if next_node not in used:
                    if target_node is not None:
                        parents[next_node] = node
                        if node == target_node:
                            break
                    if next_node in stop_nodes:
                        visited_stops.add(next_node)
                        continue
                    new_used_nodes.add(next_node)
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
        return new_used_nodes, visited_stops


def _find_path(start_nodes, target_node, reverse_order=False):
    """
    Returns
    ---------------
    path
        The minimal path from one of the `start_nodes` to the `target_node`
    """
    return _bfs(start_nodes, target_node=target_node, reverse_order=reverse_order)


def _find_candidate(traverse_queue, path_to_target, pos_in_path, suffix_nodes, cur_cand_pos, used: Set, reverse_order=False, cand_filter: NodeFilter = NodeFilter()):
    '''
    :return:
        new_candidate
        new nodes that are inside the hammock

        returns the `target_node` if none of the candidates are permitted by the `cand_filter`
    '''

    def reduce_suffix_by(k):
        nonlocal traverse_queue, cur_cand_pos, used
        for _ in range(0, k):
            if cur_cand_pos >= 0:
                traverse_queue.add(path_to_target[cur_cand_pos])
                suffix_nodes.remove(path_to_target[cur_cand_pos])
            cur_cand_pos += 1
            if cur_cand_pos >= len(path_to_target):
                raise Exception("Path length exceeded")

    used_nodes = set()
    while True:
        new_cand_pos = cur_cand_pos
        while traverse_queue:
            new_used_nodes, visited_suffix_nodes = _bfs(traverse_queue, stop_nodes=suffix_nodes, used=used,
                                                        reverse_order=reverse_order)
            traverse_queue.clear()
            used_nodes = used_nodes.union(new_used_nodes)

            for node in visited_suffix_nodes:
                new_cand_pos = max(new_cand_pos, pos_in_path[node])
            if new_cand_pos > cur_cand_pos:
                reduce_suffix_by(new_cand_pos - cur_cand_pos)

        if new_cand_pos + 1 == len(path_to_target) or cand_filter.is_permitted(path_to_target[new_cand_pos]):
            break
        reduce_suffix_by(1)

    return new_cand_pos, used_nodes


def _find_source_candidate(traverse_queue, path_to_target, pos_in_path, suffix_nodes, cur_cand_pos, used: Set, parameters=None):
    source_node_type = exec_utils.get_param_value(Parameters.PARAM_SOURCE_NODE_TYPE, parameters, NodeTypes.PLACE_TYPE)
    return _find_candidate(traverse_queue, path_to_target, pos_in_path, suffix_nodes, cur_cand_pos, used, reverse_order=True, cand_filter=NodeFilter(source_node_type))


def _find_sink_candidate(traverse_queue, path_to_target, pos_in_path, suffix_nodes, cur_cand_pos, used: Set, parameters=None):
    sink_node_type = exec_utils.get_param_value(Parameters.PARAM_SINK_NODE_TYPE, parameters, NodeTypes.PLACE_TYPE)
    return _find_candidate(traverse_queue, path_to_target, pos_in_path, suffix_nodes, cur_cand_pos, used, cand_filter=NodeFilter(sink_node_type))


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
        Time complexity - O(m), where m is the number of edges in the net
    """
    covered_nodes = set(covered_nodes)

    SRC = 0
    SINK = 1

    path_to = [None, None]
    path_to[SRC] = _find_path(covered_nodes, net_source, reverse_order=True)
    path_to[SINK] = _find_path(covered_nodes, net_sink)

    pos_in_path = [None, None]
    pos_in_path[SRC] = {node: pos for pos, node in enumerate(path_to[SRC])}
    pos_in_path[SINK] = {node: pos for pos, node in enumerate(path_to[SINK])}

    suffix_nodes = [None, None]
    suffix_nodes[SRC] = set(path_to[SRC])
    suffix_nodes[SINK] = set(path_to[SINK])

    used = [None, None]
    used[SRC] = set()
    used[SINK] = set()

    inside_hammock = set()
    new_inside_hammock = set(covered_nodes)

    source_cand = sink_cand = 0

    while new_inside_hammock:
        source_cand, src_new_inside = _find_source_candidate(copy(new_inside_hammock), path_to[SRC], pos_in_path[SRC], suffix_nodes[SRC], source_cand, used[SRC], parameters)
        sink_cand, sink_new_inside = _find_sink_candidate(copy(new_inside_hammock), path_to[SINK], pos_in_path[SINK], suffix_nodes[SINK], sink_cand, used[SINK], parameters)
        inside_hammock = inside_hammock.union(new_inside_hammock)
        new_inside_hammock = src_new_inside.union(sink_new_inside).difference(new_inside_hammock)

        # expand
        for arc in path_to[SRC][source_cand].out_arcs:
            cur_node = arc.target
            if cur_node not in inside_hammock:
                new_inside_hammock.add(cur_node)
        for arc in path_to[SINK][sink_cand].in_arcs:
            cur_node = arc.source
            if cur_node not in inside_hammock:
                new_inside_hammock.add(cur_node)

    hammock_src = path_to[SRC][source_cand]
    hammock_sink = path_to[SINK][sink_cand]
    return Hammock(hammock_src, hammock_sink, inside_hammock.union({hammock_src, hammock_sink}))
