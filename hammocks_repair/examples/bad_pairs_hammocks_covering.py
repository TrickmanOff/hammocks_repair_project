from hammocks_repair.examples import test_net
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.objects.conversion.log import converter
from hammocks_repair.utils import net_helpers
from hammocks_repair.visualization import net_visualize
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.petri_net.common import visualize
from hammocks_repair.examples.test_net import Variants


from hammocks_repair.conformance_analysis import bad_pairs_selection
from hammocks_repair.hammocks_covering import algorithm as hammocks_covering_algo

from pm4py.objects.petri_net.utils import petri_utils
from pm4py.util import exec_utils
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo

import hammocks_repair.net_repair.hammocks_replacement.algorithm as hammocks_replacement
import hammocks_repair.net_repair.naive_log_only.algorithm as naive_log_only
from hammocks_repair.grader.utils import timeit

import time
import os

'''
functions in this module repeat the corresponding algorithms but with
visualization of intermediate step

so each function SHOULD BE REWRITTEN in case of significant changes in the corresponding functions
'''


def visualize_naive_log_repair(net, init_marking, final_marking, log, parameters=None,
                               alignments=None,
                               repaired_net_filename='images/10-repaired_naive_logonly.png'):
    rep_net, rep_init_marking, rep_final_marking = naive_log_only.apply(net, init_marking,
                                                                        final_marking, log,
                                                                        alignments,
                                                                        parameters)
    new_transitions = []
    for trans in rep_net.transitions:
        if petri_utils.get_transition_by_name(net, trans.name) is None:
            new_transitions.append(trans)
    decorations = net_visualize.paint_nodes(new_transitions)
    if repaired_net_filename is not None:
        pn_visualizer.save(
            visualize.apply(rep_net, rep_init_marking, rep_final_marking, decorations=decorations),
            repaired_net_filename)
    return rep_net, rep_init_marking, rep_final_marking


def calc_alignments_stats(alignments):
    '''
    :return:
        'model_only'
    '''
    log_only_moves_cnt = 0
    model_only_moves_cnt = 0

    for alignment_info in alignments:
        alignment = alignment_info['alignment']

        for move in alignment:
            (log_name, model_name), (log_label, model_label) = move
            if model_label == '>>':  # log.xes-only move
                log_only_moves_cnt += 1
            elif log_label == '>>' and model_label is not None:  # model-only move (excluding hidden transitions)
                model_only_moves_cnt += 1

    return {'log_only': log_only_moves_cnt,
            'model_only': model_only_moves_cnt}


def visualize_hammocks_replacement_repair(net, init_marking, final_marking, log, alignments=None,
                                          parameters=None,
                                          visualization_folder='images',
                                          prerepaired_net_filename='10-prerepaired.png',
                                          bad_pairs_filename='20-bad_pairs.png',
                                          covering_hammocks_filename='30-bad_pairs_hammock.png',
                                          repaired_net_filename='40-repaired_hammocks.png',
                                          calc_stats=False):
    '''
    apply hammocks repair and visualize its steps
    :return
        net, init_marking, final_marking

        stats (if calc_stats == True)
        'alignments': {
            'log_only_before_prerepair': ,
            'model_only_after_prerepair': ,
        },
        'time': {
            'alignments': ---,
            'prerepair': ---,
            'hammocks_replacement': ---,
        }
    '''
    if not os.path.exists(visualization_folder):
        os.makedirs(visualization_folder)

    prerepaired_net_filename = os.path.join(visualization_folder, prerepaired_net_filename)
    bad_pairs_filename = os.path.join(visualization_folder, bad_pairs_filename)
    covering_hammocks_filename = os.path.join(visualization_folder, covering_hammocks_filename)
    repaired_net_filename = os.path.join(visualization_folder, repaired_net_filename)

    stats = {}
    stats['time'] = {
        'alignments': 0,
        'prerepair': 0,
        'hammocks_replacement': 0,
    }
    stats['alignments'] = {}

    alignments_parameters = {
        alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
    }
    # alignments
    wall_time, alignments = timeit(alignments_algo.apply_log)(log, net, init_marking, final_marking,
                                                              parameters=alignments_parameters)
    stats['time']['alignments'] += wall_time

    alignment_stats = calc_alignments_stats(alignments)
    stats['alignments']['log_only_moves_before_prerepair'] = alignment_stats['log_only']
    stats['alignments']['model_only_moves_before_prerepair'] = alignment_stats['model_only']
    #

    # prerepair
    prerepair_variant = exec_utils.get_param_value(
        hammocks_replacement.Parameters.PREREPAIR_VARIANT, parameters,
        hammocks_replacement.DEFAULT_PREREPAIR_VARIANT)
    if prerepair_variant is not None:
        prerepair_func = visualization_variants[prerepair_variant]
        wall_time, (net, init_marking, final_marking) = timeit(prerepair_func)(net, init_marking, final_marking, log,
                                                                             parameters, alignments,
                                                                             prerepaired_net_filename)
        stats['time']['prerepair'] += wall_time

    # hardcode for each possible prerepair_variants (that's probably not the best solution)
    if prerepair_variant == hammocks_replacement.PrerepairVariants.NAIVE_LOG_ONLY.value:
        if parameters.get(hammocks_replacement.naive_log_only_algo.Parameters.ALIGNMENTS_MODIFICATION_MODE,
                          hammocks_replacement.naive_log_only_algo.DEFAULT_MODIFY_ALIGNMENTS_MODE) == hammocks_replacement.naive_log_only_algo.AlignmentsModificationMode.NONE:
            alignments = None

    if alignments is None:
        print('alignments were recalculated')
        wall_time, alignments = timeit(alignments_algo.apply_log)(log, net, init_marking, final_marking,
                                                                  parameters=alignments_parameters)
        stats['time']['alignments'] += wall_time

    alignment_stats = calc_alignments_stats(alignments)
    stats['alignments']['log_only_moves_after_prerepair'] = alignment_stats['log_only']
    stats['alignments']['model_only_moves_after_prerepair'] = alignment_stats['model_only']

    # bad pairs
    wall_time, bad_pairs = timeit(bad_pairs_selection.apply)(net, init_marking, final_marking, alignments)
    stats['time']['hammocks_replacement'] += wall_time

    # find covering hammocks
    wall_time, hammocks = timeit(hammocks_covering_algo.apply)(net, bad_pairs.keys(), as_pairs=True, parameters=parameters)
    stats['time']['hammocks_replacement'] += wall_time

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

    decorations = {}
    rep_net, rep_init_marking, rep_final_marking = net, init_marking, final_marking

    # discovering subprocesses and replacing hammocks with them
    for hammock in hammocks:
        st_time = time.time()
        subproc_net, subproc_src, subproc_sink = hammocks_replacement.discover_subprocess(
            hammock, log, parameters)
        hammocks_replacement.replace_hammock(rep_net, rep_init_marking,
                                             rep_final_marking, hammock,
                                             subproc_net, subproc_src, subproc_sink)
        end_time = time.time()
        stats['time']['hammocks_replacement'] += end_time - st_time

        subproc_nodes = list(subproc_net.places) + list(subproc_net.transitions)
        decorations = net_visualize.paint_nodes(subproc_nodes, decorations=decorations)

    net_helpers.enumerate_nodes_successively(rep_net)

    # repaired net
    if repaired_net_filename is not None:
        pn_visualizer.save(
            visualize.apply(rep_net, rep_init_marking, rep_final_marking, decorations=decorations),
            repaired_net_filename)

    if calc_stats:
        for time_key in stats['time'].keys():
            stats['time'][time_key] = round(stats['time'][time_key], 2)
        return rep_net, rep_init_marking, rep_final_marking, stats
    else:
        return rep_net, rep_init_marking, rep_final_marking


visualization_variants = {
    hammocks_replacement: visualize_hammocks_replacement_repair,
    naive_log_only: visualize_naive_log_repair,
}


def get_sample_data(case=Variants.CASE1):
    model_net, model_init_marking, model_final_marking, \
        real_net, real_init_marking, real_final_marking = test_net.get_case(case)

    sim_log = pn_playout.apply(real_net, real_init_marking, real_final_marking)
    df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
    filtered_sim_log = end_activities_filter.apply(df, ['sell device', 'received payment',
                                                        'court'])  # traces only with valid last activities
    filtered_sim_log = converter.apply(filtered_sim_log, variant=converter.Variants.TO_EVENT_LOG)

    return model_net, model_init_marking, model_final_marking, real_net, real_init_marking, real_final_marking, filtered_sim_log


def visualize_sample_repair(case=Variants.CASE1, parameters=None,
                            algo=hammocks_replacement):
    '''
    modes:

    possible causes of model-only moves in alignment:
    1. wrong order of activities
    2. outdated activities
    '''
    if parameters is None:
        parameters = {}

    default_parameters = {
        hammocks_replacement.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: hammocks_replacement.NodeTypes.PLACE_TYPE | hammocks_replacement.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        hammocks_replacement.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: hammocks_replacement.NodeTypes.PLACE_TYPE | hammocks_replacement.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        hammocks_replacement.Parameters.SUBPROCESS_MINER_ALGO: inductive_miner,  # default value
    }
    for param, value in default_parameters.items():
        if param not in parameters:
            parameters[param] = value

    model_net, model_init_marking, model_final_marking, \
        real_net, real_init_marking, real_final_marking, filtered_sim_log = get_sample_data(case)

    model_net_viz = pn_visualizer.apply(model_net, model_init_marking, model_final_marking)
    pn_visualizer.save(model_net_viz, 'images/00-model_net.png')
    real_process_net_viz = pn_visualizer.apply(real_net, real_init_marking, real_final_marking)
    pn_visualizer.save(real_process_net_viz, 'images/01-real_net.png')

    return visualization_variants[algo](model_net, model_init_marking, model_final_marking,
                                        filtered_sim_log, parameters=parameters)
