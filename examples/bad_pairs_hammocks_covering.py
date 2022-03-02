from examples import test_net
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.objects.conversion.log import converter
from copy import copy, deepcopy
from utils import net_helpers
from net_repair import algorithm as net_repair_algo
from visualization import net_visualize
from pm4py.visualization.petri_net import visualizer as pn_visualizer


def case1():
    '''
    delete admit_helplessness

    :return
        model_net, ...,
        real_process_net, ...
    '''
    model_net, model_init_marking, model_final_marking = test_net.create_net()
    real_net, real_init_marking, real_final_marking = test_net.create_net()

    net_helpers.del_trans('admit_helplessness_hidden_t', model_net)

    return model_net, model_init_marking, model_final_marking, \
           real_net, real_init_marking, real_final_marking


def case2():
    '''
    - simpler 'troubles with client' segment
    - only one vendor
    '''

    model_net, model_init_marking, model_final_marking = test_net.create_net()
    real_net, real_init_marking, real_final_marking = test_net.create_net()
    # troubles with client
    net_helpers.del_trans('client came', model_net)
    net_helpers.del_trans('client didnt come', model_net)
    net_helpers.del_trans('sell device', model_net)
    net_helpers.del_trans('court', model_net)

    net_helpers.del_place('p15', model_net)
    net_helpers.del_place('p16', model_net)

    net_helpers.create_arc('p14', 'received payment', model_net)
    net_helpers.create_arc('p14', 'troubles with client', model_net)

    net_helpers.add_transition('call bob', model_net)
    net_helpers.create_arc('p3', 'call bob', model_net)
    net_helpers.create_arc('call bob', 'end', model_net)

    # vendor
    net_helpers.del_place('p8', model_net)
    net_helpers.del_place('p11', model_net)

    net_helpers.del_trans('2nd vendor', model_net)
    net_helpers.del_trans('no_2nd_vendor_hidden_t', model_net)
    net_helpers.del_trans('no_1st_vendor_hidden_t', model_net)
    net_helpers.del_trans('no_parts_hidden_t', model_net)

    return model_net, model_init_marking, model_final_marking, \
           real_net, real_init_marking, real_final_marking


worsening_modes = {
    1: case1,
    2: case2
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
        pn_visualizer.save(
            net_visualize.visualize_pairs(bad_pairs, net, init_marking, final_marking),
            bad_pairs_filename)

    # covering hammocks visualization
    if covering_hammocks_filename is not None:
        pn_visualizer.save(net_visualize.visualize_hammocks(net, hammocks, covered_nodes),
                           covering_hammocks_filename)


def print_bad_pairs_hammock(mode=1):
    '''
    modes: 1

    possible causes of model-only moves in alignment:
    1. wrong order of activities
    2. outdated activities
    '''

    model_net, model_init_marking, model_final_marking, \
    real_net, real_init_marking, real_final_marking = worsening_modes[mode]()

    sim_log = pn_playout.apply(real_net, real_init_marking, real_final_marking)
    df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
    filtered_sim_log = end_activities_filter.apply(df, ['sell device', 'received payment',
                                                        'court'])  # traces only with valid last activities
    filtered_sim_log = converter.apply(filtered_sim_log, variant=converter.Variants.TO_EVENT_LOG)

    model_net_viz = pn_visualizer.apply(model_net, model_init_marking, model_final_marking)
    pn_visualizer.save(model_net_viz, 'images/model_net.png')
    real_process_net_viz = pn_visualizer.apply(real_net, real_init_marking, real_final_marking)
    pn_visualizer.save(real_process_net_viz, 'images/real_net.png')

    visualize_net_repair(model_net, model_init_marking, model_final_marking, filtered_sim_log)
