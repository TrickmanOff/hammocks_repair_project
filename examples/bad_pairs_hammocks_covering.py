from examples import test_net
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from pm4py.objects.conversion.log import converter
from utils import net_helpers
from visualization import net_visualize
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.petri_net.common import visualize
from examples.test_net import Variants

from pm4py.objects.petri_net.utils import petri_utils
from pm4py.util import exec_utils
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo

import net_repair.hammocks_replacement.algorithm as hammocks_replacement
import net_repair.naive_log_only.algorithm as naive_log_only


'''
functions in this module repeat the corresponding algorithms but with
visualization of intermediate step

so each function SHOULD BE REWRITTEN in case of changes in the corresponding functions
'''


def visualize_naive_log_repair(net, init_marking, final_marking, log, parameters=None,
                               alignments=None,
                               repaired_net_filename='images/10-repaired_naive_logonly.png'):
    rep_net, rep_init_marking, rep_final_marking = naive_log_only.apply(net, init_marking,
                                                                         final_marking, log, alignments,
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


def visualize_hammocks_replacement_repair(net, init_marking, final_marking, log, alignments=None,
                                          parameters=None,
                                          prerepaired_net_filename='images/10-prerepaired.png',
                                          bad_pairs_filename='images/20-bad_pairs.png',
                                          covering_hammocks_filename='images/30-bad_pairs_hammock.png',
                                          repaired_net_filename='images/40-repaired_hammocks.png'):
    '''
    apply hammocks repair and visualize its steps
    '''

    alignments_parameters = {
        alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
    }
    alignments = alignments_algo.apply_log(log, net, init_marking, final_marking,
                                           parameters=alignments_parameters)

    # prerepair
    prerepair_variant = exec_utils.get_param_value(
        hammocks_replacement.Parameters.PREREPAIR_VARIANT, parameters,
        hammocks_replacement.DEFAULT_PREREPAIR_VARIANT)
    if prerepair_variant is not None:
        prerepair_func = visualization_variants[prerepair_variant]
        net, init_marking, final_marking = prerepair_func(net, init_marking, final_marking, log,
                                                          parameters, alignments,
                                                          prerepaired_net_filename)

    should_recalculate_alignments = False
    supress_logonly_in_alignments = exec_utils.get_param_value(
        hammocks_replacement.Parameters.SUPRESS_LOGONLY_IN_ALIGNMENTS, parameters, True)
    if prerepair_variant is None:
        if alignments is None:
            should_recalculate_alignments = True
    elif supress_logonly_in_alignments:
        if prerepair_variant == hammocks_replacement.PrerepairVariants.NAIVE_LOG_ONLY.value:
            if parameters.get(naive_log_only.Parameters.MODIFY_ALIGNMENTS_MODE,
                              naive_log_only.DEFAULT_MODIFY_ALIGNMENTS_MODE) is naive_log_only.ModifyAlignments.NONE:
                should_recalculate_alignments = True
        # hardcode for each possible prerepair_variants (that's probably not the best solution)
        
    if should_recalculate_alignments:
        print('alignments were recalculated')
        supress_logonly_in_alignments = exec_utils.get_param_value(hammocks_replacement.Parameters.SUPRESS_LOGONLY_IN_ALIGNMENTS, parameters, True)
        if supress_logonly_in_alignments:
            print('  using custom cost function')
            parameters = hammocks_replacement.use_custom_cost_function(net, alignments, parameters)
        alignments = alignments_algo.apply_log(log, net, init_marking, final_marking, parameters=alignments_parameters)

    # hammocks replacement
    hammocks, bad_pairs = hammocks_replacement.find_bad_hammocks(net, init_marking,
                                                                                                 final_marking,
                                                                                                 alignments,
                                                                                                 parameters=parameters)

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
        subproc_net, subproc_src, subproc_sink = hammocks_replacement.discover_subprocess(
            hammock, log, parameters)
        hammocks_replacement.replace_hammock(rep_net, rep_init_marking,
                                                                             rep_final_marking, hammock,
                                                                             subproc_net, subproc_src, subproc_sink)
        subproc_nodes = list(subproc_net.places) + list(subproc_net.transitions)
        decorations = net_visualize.paint_nodes(subproc_nodes, decorations=decorations)

    # repaired net
    if repaired_net_filename is not None:
        pn_visualizer.save(
            visualize.apply(rep_net, rep_init_marking, rep_final_marking, decorations=decorations),
            repaired_net_filename)

    return rep_net, rep_init_marking, rep_final_marking


visualization_variants = {
    hammocks_replacement: visualize_hammocks_replacement_repair,
    naive_log_only: visualize_naive_log_repair,
}


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
    real_net, real_init_marking, real_final_marking = test_net.get_case(case)

    sim_log = pn_playout.apply(real_net, real_init_marking, real_final_marking)
    df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
    filtered_sim_log = end_activities_filter.apply(df, ['sell device', 'received payment',
                                                        'court'])  # traces only with valid last activities
    filtered_sim_log = converter.apply(filtered_sim_log, variant=converter.Variants.TO_EVENT_LOG)

    model_net_viz = pn_visualizer.apply(model_net, model_init_marking, model_final_marking)
    pn_visualizer.save(model_net_viz, 'images/00-model_net.png')
    real_process_net_viz = pn_visualizer.apply(real_net, real_init_marking, real_final_marking)
    pn_visualizer.save(real_process_net_viz, 'images/01-real_net.png')

    return visualization_variants[algo](model_net, model_init_marking, model_final_marking,
                                          filtered_sim_log, parameters=parameters)
