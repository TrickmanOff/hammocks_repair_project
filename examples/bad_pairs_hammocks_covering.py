from examples import test_net
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.objects.conversion.log import converter
from copy import copy, deepcopy
from utils import net_helpers
from net_repair import algorithm as net_repair_algo
from visualization import net_visualize
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from examples.test_net import Variants
import examples.test_net
from net_repair import algorithm as net_repair_algo

from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.alpha import algorithm as alpha_miner


def visualize_net_repair(net, init_marking, final_marking, log, parameters=None,
                         bad_pairs_filename='images/bad_pairs.png',
                         covering_hammocks_filename='images/bad_pairs_hammock.png',
                         repaired_net_filename='images/repaired_hammocks.png'):
    '''
    apply hammocks repair and visualize its steps
    '''

    hammocks, bad_pairs = net_repair_algo.find_bad_hammocks(net, init_marking, final_marking,
                                                            log, parameters=parameters)

    covered_nodes = [pair[0] for pair in bad_pairs.keys()] + [pair[1] for pair in bad_pairs.keys()]
    # bad pairs visualization
    if bad_pairs_filename is not None:
        pn_visualizer.save(
            net_visualize.visualize_pairs(bad_pairs, net, init_marking, final_marking),
            bad_pairs_filename)

    # covering hammocks visualization
    if covering_hammocks_filename is not None:
        pn_visualizer.save(net_visualize.visualize_hammocks(net, hammocks, covered_nodes),
                           covering_hammocks_filename)

    # repaired net
    rep_net, rep_init_marking, rep_final_marking = net_repair_algo.apply(net, init_marking, final_marking, log, parameters)
    if repaired_net_filename is not None:
        pn_visualizer.save(pn_visualizer.apply(rep_net, rep_init_marking, rep_final_marking),
                           repaired_net_filename)


def print_bad_pairs_hammock(case=Variants.CASE1):
    '''
    modes: 1

    possible causes of model-only moves in alignment:
    1. wrong order of activities
    2. outdated activities
    '''

    parameters = {
        net_repair_algo.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: net_repair_algo.NodeTypes.PLACE_TYPE | net_repair_algo.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        net_repair_algo.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: net_repair_algo.NodeTypes.PLACE_TYPE | net_repair_algo.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        net_repair_algo.Parameters.SUBPROCESS_MINER_ALGO: inductive_miner,  # default value
    }

    model_net, model_init_marking, model_final_marking, \
    real_net, real_init_marking, real_final_marking = test_net.get_case(case)

    sim_log = pn_playout.apply(real_net, real_init_marking, real_final_marking)
    df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
    filtered_sim_log = end_activities_filter.apply(df, ['sell device', 'received payment',
                                                        'court'])  # traces only with valid last activities
    filtered_sim_log = converter.apply(filtered_sim_log, variant=converter.Variants.TO_EVENT_LOG)

    model_net_viz = pn_visualizer.apply(model_net, model_init_marking, model_final_marking)
    pn_visualizer.save(model_net_viz, 'images/model_net.png')
    real_process_net_viz = pn_visualizer.apply(real_net, real_init_marking, real_final_marking)
    pn_visualizer.save(real_process_net_viz, 'images/real_net.png')

    visualize_net_repair(model_net, model_init_marking, model_final_marking, filtered_sim_log, parameters=parameters)
