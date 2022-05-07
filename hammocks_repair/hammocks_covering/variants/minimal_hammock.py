from copy import copy
from typing import Optional, Dict, Any, Union, Iterable
from enum import Enum

from pm4py.objects.petri_net.obj import PetriNet
from pm4py.util import exec_utils

from hammocks_repair.hammocks_covering.obj import Hammock


class Parameters(Enum):
    PARAM_SOURCE_NODE_TYPE = 'source_node_type'
    PARAM_SINK_NODE_TYPE = 'sink_node_type'


class NodeTypes:
    PLACE_TYPE = (1 << 0)
    NOT_HIDDEN_TRANS_TYPE = (1 << 1)
    HIDDEN_TRANS_TYPE = (1 << 2)


DEFAULT_SOURCE_NODE_TYPE = NodeTypes.PLACE_TYPE
DEFAULT_SINK_NODE_TYPE = NodeTypes.PLACE_TYPE


class NodeFilter:
    def __init__(self, permitted_types=NodeTypes.PLACE_TYPE):
        self.__permitted_types = permitted_types

    def is_permitted(self, obj: Union[PetriNet.Place, PetriNet.Transition]):
        if isinstance(obj, PetriNet.Place):
            return self.__permitted_types & NodeTypes.PLACE_TYPE
        else:
            if obj.label is None:  # hidden transition
                return self.__permitted_types & NodeTypes.HIDDEN_TRANS_TYPE
            else:
                return self.__permitted_types & NodeTypes.NOT_HIDDEN_TRANS_TYPE


def _get_source_filter(parameters):
    source_node_type = exec_utils.get_param_value(Parameters.PARAM_SOURCE_NODE_TYPE, parameters, DEFAULT_SOURCE_NODE_TYPE)
    return NodeFilter(source_node_type)


def _get_sink_filter(parameters):
    sink_node_type = exec_utils.get_param_value(Parameters.PARAM_SINK_NODE_TYPE, parameters, NodeTypes.PLACE_TYPE)
    return NodeFilter(sink_node_type)


def _find_path(start_nodes, target_node, reverse_order=False):
    """
    Returns
    ------------
    path
        The minimal path from one of the `start_nodes` to the `target_node`
    """
    node_parent = {node: None for node in start_nodes}
    used = set(start_nodes)
    cur_level = list(start_nodes)

    while cur_level:
        next_level = []
        for node in cur_level:
            if node == target_node:  # path found
                cur_level.clear()
                break

            for arc in (node.in_arcs if reverse_order else node.out_arcs):
                next_node = (arc.source if reverse_order else arc.target)
                if next_node in used:
                    continue
                node_parent[next_node] = node

                used.add(next_node)
                next_level.append(next_node)
        cur_level = next_level

    if target_node not in node_parent:
        raise Exception("The target_node is not reachable from the given set of nodes")
    path = []
    cur_node = target_node
    while cur_node is not None:
        path.append(cur_node)
        cur_node = node_parent[cur_node]
    path.reverse()
    return path


def _in_neighbors(node):
    return [in_arc.source for in_arc in node.in_arcs]


def _out_neighbors(node):
    return [out_arc.target for out_arc in node.out_arcs]


def apply(covered_nodes: Iterable[Union[PetriNet.Place, PetriNet.Transition]],
          net_source: PetriNet.Place, net_sink: PetriNet.Place,
          parameters: Optional[Dict[Any, Any]] = None) -> Hammock:
    """
    Find the minimal hammock that covers the `covered_nodes`
    Time complexity - O(n + m), where m is the number of edges in the net and n is the number of nodes in it

    Parameters
    ------------
    covered_nodes
        The set of nodes to cover
    net_source
        The source node of the net
    net_sink
        The sink node of the net
    parameters
        Parameters of the algorithm:
            - Parameters.PARAM_SOURCE_NODE_TYPE - permitted node type of the hammock's source (ORed NodeTypes), by default: DEFAULT_SOURCE_NODE_TYPE
            - Parameters.PARAM_SINK_NODE_TYPE - permitted node type of the hammock's source (ORed NodeTypes), by default: DEFAULT_SINK_NODE_TYPE

    Returns
    ------------
    hammock
        The minimal hammock that covers the `covered_nodes`
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

    path_to_set = [None, None]
    path_to_set[SRC] = set(path_to[SRC])
    path_to_set[SINK] = set(path_to[SINK])

    node_filter = [None, None]
    node_filter[SRC] = _get_source_filter(parameters)
    node_filter[SINK] = _get_sink_filter(parameters)

    # setting up the initial condition for the algorithm
    src_ind = sink_ind = -1
    black = set()
    gray = set()
    new_nodes = copy(covered_nodes)
    ham_src = ham_sink = None

    while new_nodes:
        # step 1
        new_src_ind = src_ind
        new_sink_ind = sink_ind

        while new_src_ind != len(path_to[SRC]) - 1 and not node_filter[SRC].is_permitted(path_to[SRC][new_src_ind]):
            new_src_ind += 1
        while new_sink_ind != len(path_to[SINK]) - 1 and not node_filter[SINK].is_permitted(path_to[SINK][new_sink_ind]):
            new_sink_ind += 1

        for u in new_nodes:
            if u in path_to_set[SRC]:
                new_src_ind = max(new_src_ind, pos_in_path[SRC][u])
            if u in path_to_set[SINK]:
                new_sink_ind = max(new_sink_ind, pos_in_path[SINK][u])

        ham_src = path_to[SRC][new_src_ind]
        ham_sink = path_to[SINK][new_sink_ind]

        for u in new_nodes:
            if u != ham_src and u != ham_sink:
                gray.add(u)
        new_nodes.clear()

        # step 2
        if new_src_ind != src_ind:
            for i in range(max(0, src_ind), new_src_ind):
                gray.add(path_to[SRC][i])
            if ham_src != ham_sink:
                for u in _out_neighbors(ham_src):
                    if u not in black and u not in gray:
                        new_nodes.add(u)
            src_ind = new_src_ind
        if new_sink_ind != sink_ind:
            for i in range(max(0, sink_ind), new_sink_ind):
                gray.add(path_to[SINK][i])
            if ham_src != ham_sink:
                for u in _in_neighbors(ham_sink):
                    if u not in black and u not in gray:
                        new_nodes.add(u)
            sink_ind = new_sink_ind

        # step 3
        for u in gray:
            for v in _in_neighbors(u) + _out_neighbors(u):
                if v not in black and v not in gray:
                    new_nodes.add(v)
            black.add(u)
        gray.clear()

    return Hammock(ham_src, ham_sink, black.union({ham_src, ham_sink}))
