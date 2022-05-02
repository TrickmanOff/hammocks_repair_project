from .. import utils

from pm4py.objects.petri_net.obj import PetriNet
import pm4py.objects.petri_net.utils.networkx_graph as networkx_graph

import networkx
from Levenshtein import distance as lev_dist
from func_timeout import func_timeout, FunctionTimedOut


def conv_pn_to_graph(net):
    g, inv_dict = networkx_graph.create_networkx_directed_graph(net)

    # add info for each node in the graph
    for g_node_ind, pn_node in inv_dict.items():
        node_info = {}
        node_info['type'] = 'transition' if isinstance(pn_node, PetriNet.Transition) else 'place'

        if node_info['type'] == 'transition':
            node_info['is_hidden'] = (pn_node.label is None)
            node_info['label'] = pn_node.label

        for key, val in node_info.items():
            g.nodes[g_node_ind][key] = val
    return g


def generate_infinitely(generator, best_val):
    '''
    best_val: [value]
    infinite cycle
    '''

    for x in generator:
        best_val[0] = x


def pn_edit_similarity(net1, net2, we=0.5, wn=0.5, ws=0.1, exec_timeout=5):
    '''
    :param we:
        weight of edge insertions/deletions
    :param wn:
        weight of nodes insertions/deletions
    :param ws:
        weight of transitions substitution
    :param exec_timeout
        timeout in seconds
    '''
    we = 0.5
    wn = 0.5
    ws = 1.

    g1 = conv_pn_to_graph(net1)
    g2 = conv_pn_to_graph(net2)

    def edge_ins_cost(e):
        return we / (len(g1.edges) + len(g2.edges))

    def node_ins_cost(e):
        return wn / (len(g1.nodes) + len(g2.nodes))

    def node_subst_cost(n1, n2):
        if n1['type'] == 'place' and n2['type'] == 'place':
            return 0
        elif n1['type'] == 'place' or n2['type'] == 'place':
            return float('inf')
        elif n1['is_hidden'] and n2['is_hidden']:
            return 0
        elif n1['is_hidden'] or n2['is_hidden']:
            return float('inf')
        else:
            return ws * lev_dist(n1['label'], n2['label']) / max(len(g1.nodes), len(g2.nodes))

    # one run is necessary
    gen = networkx.optimize_graph_edit_distance(g1, g2,
                                                       node_subst_cost=node_subst_cost, node_del_cost=node_ins_cost, node_ins_cost=node_ins_cost,
                                                       edge_del_cost=edge_ins_cost, edge_ins_cost=edge_ins_cost)

    wall_time, first_approx = utils.timeit(next)(gen)
    print(f'{round(wall_time, 2)} secs spent on finding an approximation of graph edit distance')
    edit_diff = [first_approx]
    try:
        func_timeout(exec_timeout, generate_infinitely, args=(gen, edit_diff))
    except FunctionTimedOut:
        pass
    return 1. - edit_diff[0]
