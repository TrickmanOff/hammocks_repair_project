from hammocks_covering.examples.test_net import create_net
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from hammocks_covering.examples.net_helpers import get_transition_by_label
from hammocks_covering import algorithm as hammocks_covering
import hammock_vis


def print_min_hammock():
    net, init_marking, final_marking = create_net()
    # viz = pn_visualizer.apply(net, init_marking, final_marking)
    # pn_visualizer.save(viz, 'images/sample.png')

    order_parts_t = get_transition_by_label(net, 'order parts')
    sec_vendor_t = get_transition_by_label(net, '2nd vendor')
    add_to_the_db_t = get_transition_by_label(net, 'add to the db')
    inspect_t = get_transition_by_label(net, 'inspect')

    covered_nodes = [add_to_the_db_t, inspect_t]
    # covered_nodes = [order_parts_t, sec_vendor_t]

    parameters = {
        hammocks_covering.Parameters.HAMMOCK_SOURCE_NODE_TYPE: hammocks_covering.NodeTypes.PLACE_TYPE | hammocks_covering.NodeTypes.NOT_HIDDEN_TRANS_TYPE | hammocks_covering.NodeTypes.HIDDEN_TRANS_TYPE,
        hammocks_covering.Parameters.HAMMOCK_SINK_NODE_TYPE: hammocks_covering.NodeTypes.PLACE_TYPE | hammocks_covering.NodeTypes.NOT_HIDDEN_TRANS_TYPE | hammocks_covering.NodeTypes.HIDDEN_TRANS_TYPE
    }

    min_hammock = hammocks_covering.apply(net, covered_nodes, parameters=parameters)
    viz = hammock_vis.visualize_hammock(net, min_hammock, covered_nodes)
    pn_visualizer.save(viz, 'images/hammock.png')
