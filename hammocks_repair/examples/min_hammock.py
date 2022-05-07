from hammocks_repair.examples import test_net
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from hammocks_repair.utils.net_helpers import find_transition
from hammocks_repair.hammocks_covering import algorithm as hammocks_covering
from hammocks_repair.visualization import net_visualize
from pm4py.objects.conversion.log import converter
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from hammocks_repair.utils import net_helpers
from hammocks_repair.conformance_analysis import bad_pairs_selection

net, init_marking, final_marking = test_net.create_net()

order_parts_t = find_transition(net, 'order parts')
sec_vendor_t = find_transition(net, '2nd vendor')
add_to_the_db_t = find_transition(net, 'add to the db')
inspect_t = find_transition(net, 'inspect')
client_didnt_come_t = find_transition(net, 'client didnt come')
sell_device_t = find_transition(net, 'sell device')
complete_repair_t = find_transition(net, 'complete repair')
repair_finished_t = find_transition(net, 'repair finished')

# TODO: rewrite


def print_min_hammock():
    covered_nodes = [client_didnt_come_t, sell_device_t]
    # covered_nodes = [order_parts_t, sec_vendor_t]

    parameters = {
        hammocks_covering.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: hammocks_covering.NodeTypes.PLACE_TYPE,
        hammocks_covering.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: hammocks_covering.NodeTypes.PLACE_TYPE
    }

    min_hammock = hammocks_covering.apply(net, covered_nodes, parameters=parameters)
    viz = net_visualize.visualize_hammocks(net, [min_hammock], covered_nodes)
    pn_visualizer.save(viz, 'images/hammock.png')


def print_min_hammock_pairs():
    pairs = [
        (order_parts_t, sec_vendor_t),
        (client_didnt_come_t, sell_device_t),
        # (repair_finished_t, complete_repair_t)  # one big hammock
    ]

    pairs_vis = {(pair[0].label, pair[1].label): 1 for pair in pairs}
    viz = net_visualize.visualize_pairs(pairs_vis, net, init_marking, final_marking)
    pn_visualizer.save(viz, 'images/pairs.png')

    hammocks = hammocks_covering.apply(net, pairs, as_graph=True)
    nodes = []
    for pair in pairs:
        nodes.append(pair[0])
        nodes.append(pair[1])

    viz = net_visualize.visualize_hammocks(net, hammocks, nodes)
    pn_visualizer.save(viz, 'images/pairs_hammocks.png')


def print_bad_pair_hammock():
    sim_log = pn_playout.apply(net, init_marking, final_marking)
    df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
    filtered_log = end_activities_filter.apply(df, ['sell device', 'received payment', 'court'])

    net_helpers.del_trans('admit_helplessness_hidden_t', net)

    bad_ps = bad_pairs_selection.apply(net, init_marking, final_marking, converter.apply(df, variant=converter.Variants.TO_EVENT_LOG))
    pairs = [(find_transition(net, p[0]), find_transition(p[1], net)) for p in bad_ps.keys()]
    hammocks = hammocks_covering.apply(net, pairs, as_graph=True)

    nodes = []
    for pair in pairs:
        nodes.append(pair[0])
        nodes.append(pair[1])

    viz = net_visualize.visualize_hammocks(net, hammocks, nodes)
    pn_visualizer.save(viz, 'images/bad_pair_hammock.png')
