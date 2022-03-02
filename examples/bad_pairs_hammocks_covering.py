from examples import test_net
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.objects.conversion.log import converter
from copy import copy
from utils import net_helpers
from net_repair import algorithm as net_repair_algo
from visualization import net_visualize
from pm4py.visualization.petri_net import visualizer as pn_visualizer


def worsen_net_1(net):
    '''
    delete admit_helplessness
    '''
    net = copy(net)
    net_helpers.del_trans('admit_helplessness_hidden_t', net)
    return net


worsening_modes = {
    1: worsen_net_1
}


def visualize_net_repair(net, init_marking, final_marking, log, parameters=None,
                         bad_pairs_filename='images/bad_pairs.png',
                         covering_hammocks_filename='images/bad_pairs_hammock.png'):
    '''
    apply hammocks repair and visualize its steps
    '''

    if parameters is None:
        parameters = {
            net_repair_algo.Parameters.HAMMOCK_SOURCE_NODE_TYPE: net_repair_algo.NodeTypes.PLACE_TYPE | net_repair_algo.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
            net_repair_algo.Parameters.HAMMOCK_SINK_NODE_TYPE: net_repair_algo.NodeTypes.PLACE_TYPE | net_repair_algo.NodeTypes.NOT_HIDDEN_TRANS_TYPE
        }

    hammocks, bad_pairs = net_repair_algo.find_bad_hammocks(net, init_marking, final_marking,
                                                            log, parameters=parameters)

    covered_nodes = [pair[0] for pair in bad_pairs.keys()] + [pair[1] for pair in bad_pairs.keys()]
    # bad pairs visualization
    if bad_pairs_filename is not None:
        pn_visualizer.save(net_visualize.visualize_pairs(bad_pairs, net, init_marking, final_marking), bad_pairs_filename)

    # covering hammocks visualization
    if covering_hammocks_filename is not None:
        pn_visualizer.save(net_visualize.visualize_hammocks(net, hammocks, covered_nodes), covering_hammocks_filename)


def print_bad_pairs_hammock(mode=1):
    '''
    modes: 1
    '''
    net, init_marking, final_marking = test_net.create_net()
    sim_log = pn_playout.apply(net, init_marking, final_marking)
    df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
    filtered_sim_log = end_activities_filter.apply(df, ['sell device', 'received payment', 'court'])  # traces only with valid last activities
    filtered_sim_log = converter.apply(filtered_sim_log, variant=converter.Variants.TO_EVENT_LOG)

    net = worsening_modes[mode](net)

    worsened_net_viz = pn_visualizer.apply(net, init_marking, final_marking)
    pn_visualizer.save(worsened_net_viz, 'images/worsened_net.png')

    visualize_net_repair(net, init_marking, final_marking, filtered_sim_log)
