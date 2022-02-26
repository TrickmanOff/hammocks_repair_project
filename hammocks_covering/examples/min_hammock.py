from hammocks_covering.examples.test_net import create_net
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from hammocks_covering.examples.net_helpers import get_transition_by_label
from hammocks_covering import algorithm as hammocks_covering
import hammock_vis

net, init_marking, final_marking = create_net()

order_parts_t = get_transition_by_label(net, 'order parts')
sec_vendor_t = get_transition_by_label(net, '2nd vendor')
add_to_the_db_t = get_transition_by_label(net, 'add to the db')
inspect_t = get_transition_by_label(net, 'inspect')
client_didnt_come_t = get_transition_by_label(net, 'client didnt come')
sell_device_t = get_transition_by_label(net, 'sell device')
complete_repair_t = get_transition_by_label(net, 'complete repair')
repair_finished_t = get_transition_by_label(net, 'repair finished')


def print_min_hammock():
    covered_nodes = [client_didnt_come_t, sell_device_t]
    # covered_nodes = [order_parts_t, sec_vendor_t]

    parameters = {
        hammocks_covering.Parameters.HAMMOCK_SOURCE_NODE_TYPE: hammocks_covering.NodeTypes.PLACE_TYPE,
        hammocks_covering.Parameters.HAMMOCK_SINK_NODE_TYPE: hammocks_covering.NodeTypes.PLACE_TYPE
    }

    min_hammock = hammocks_covering.apply(net, covered_nodes, parameters=parameters)
    viz = hammock_vis.visualize_hammocks(net, [min_hammock], covered_nodes)
    pn_visualizer.save(viz, 'images/hammock.png')


def __conv_pairs_to_graph(pairs):
    graph = {}
    for a, b in pairs:
        if a not in graph:
            graph[a] = []
        graph[a].append(b)
        if b not in graph:
            graph[b] = []
        graph[b].append(a)
    return graph


def print_min_hammock_pairs():
    pairs = [
        (order_parts_t, sec_vendor_t),
        (client_didnt_come_t, sell_device_t),
        # (repair_finished_t, complete_repair_t)  # one big hammock
    ]

    pairs_vis = {(pair[0].label, pair[1].label): 1 for pair in pairs}
    viz = hammock_vis.visualize_pairs(pairs_vis, net, init_marking, final_marking)
    pn_visualizer.save(viz, 'images/pairs.png')

    hammocks = hammocks_covering.apply(net, __conv_pairs_to_graph(pairs), as_graph=True)
    nodes = []
    for pair in pairs:
        nodes.append(pair[0])
        nodes.append(pair[1])

    viz = hammock_vis.visualize_hammocks(net, hammocks, nodes)
    pn_visualizer.save(viz, 'images/pairs_hammocks.png')
