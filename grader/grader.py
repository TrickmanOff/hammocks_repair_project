from .metrics import graph_edit_similarity, graph_edit_similarity_prom
from . import utils

from examples import bad_pairs_hammocks_covering
from net_repair.hammocks_replacement import algorithm as hammocks_replacement_algo

#
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo
from pm4py.objects.conversion.log import converter
#

from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.discovery.footprints import algorithm as footprints_discovery
# from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter

from enum import Enum
import time
import pm4py
import os
import json

NET_EXT = '.pnml'
GIVEN_NET_FILENAME = 'given_net'
PERFECT_NET_FILENAME = 'perfect_net'
LOG_FOR_REPAIR_FILENAME = 'log.xes'

REPAIRED_NETS_DIR_NAME = 'repaired_nets'

VISUALIZATION_DIR_NAME = 'visualization'

GRADE_INFO_FILENAME = 'grade_info.json'


def load_grade_info(test_dir):
    filepath = os.path.join(test_dir, GRADE_INFO_FILENAME)
    if not os.path.exists(filepath):
        return {}

    with open(os.path.join(test_dir, GRADE_INFO_FILENAME), 'r') as file:
        grade_info = json.load(file)
    return grade_info


def dump_grade_info(test_dir, grade_info):
    with open(os.path.join(test_dir, GRADE_INFO_FILENAME), 'w') as file:
        json.dump(grade_info, file, indent=4)


def add_data_to_grade_info(test_dir, method_name, data):
    '''
    :param data:
        dict
    '''
    grade_info = load_grade_info(test_dir)
    if method_name not in grade_info:
        grade_info[method_name] = {}
    grade_info_cur_method = grade_info[method_name]

    for key, val_dict in data.items():
        if key not in grade_info_cur_method:
            grade_info_cur_method[key] = val_dict
        else:
            grade_info_cur_method[key] = grade_info_cur_method[key] | val_dict
    dump_grade_info(test_dir, grade_info)


def log_fitness(log, net, initial_marking, final_marking, debug=False):
    if debug:
        df_log = converter.apply(log, variant=converter.Variants.TO_DATA_FRAME)

        for i in range(len(log)):
            cur_case = log[i][0]['case:concept:name']
            df_sublog = df_log[df_log['case:concept:name'] == cur_case]
            sublog = converter.apply(df_sublog, variant=converter.Variants.TO_EVENT_LOG)
            fit = pm4py.fitness_alignments(sublog, net, initial_marking, final_marking)
            if fit['percentage_of_fitting_traces'] != 100.:
                print(i)
                print(df_sublog['concept:name'])

                alignments_parameters = {
                    alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
                }

                st_plc = None
                for pl in net.places:
                    if pl.name == 'source':
                        st_plc = pl
                alignment = alignments_algo.apply(sublog, net, initial_marking, final_marking, parameters=alignments_parameters)
                pm4py.fitness_token_based_replay(sublog, net, initial_marking, final_marking)
                dbg = 0

        ft = pm4py.fitness_alignments(log, net, initial_marking, final_marking)
    return pm4py.fitness_alignments(log, net, initial_marking, final_marking)


def footprints_similarity(net1, net1_im, net1_fm, net2, net2_im, net2_fm):
    fp_net1 = footprints_discovery.apply(net1, net1_im, net1_fm)
    fp_net2 = footprints_discovery.apply(net2, net2_im, net2_fm)

    total_matr_size = len(fp_net1['activities'])**2
    seq_rel_diff_cnt = len(fp_net1['sequence'].difference(fp_net2['sequence'])) + len(fp_net2['sequence'].difference(fp_net1['sequence']))
    par_rel_diff_cnt = len(fp_net1['parallel'].difference(fp_net2['parallel'])) + len(fp_net2['parallel'].difference(fp_net1['parallel']))

    return 1. - (seq_rel_diff_cnt + par_rel_diff_cnt) / total_matr_size


def rediscovery_time(log):
    wall_time, (net, _, _) = utils.timeit(inductive_miner.apply)(log)
    return wall_time


def load_test_dir(test_dir):
    init_test_dir(test_dir)
    given_net, given_im, given_fm = pnml_importer.apply(
        os.path.join(test_dir, GIVEN_NET_FILENAME + NET_EXT))
    perfect_net, perfect_im, perfect_fm = pnml_importer.apply(
        os.path.join(test_dir, PERFECT_NET_FILENAME + NET_EXT))
    log = xes_importer.apply(os.path.join(test_dir, LOG_FOR_REPAIR_FILENAME))

    return given_net, given_im, given_fm, \
           perfect_net, perfect_im, perfect_fm, \
           log


class Metrics(Enum):
    FITNESS = 'fitness'
    PRECISION = 'precision'
    FOOTPRINTS_SIM = 'footprints_similarity'
    EDIT_SIM = 'graph_edit_similarity'


DEFAULT_METRICS_USED = frozenset([Metrics.FITNESS, Metrics.PRECISION, Metrics.FOOTPRINTS_SIM, Metrics.EDIT_SIM])


def get_net_stats(net):
    stats = {}
    stats['places_cnt'] = len(net.places)
    stats['trans_cnt'] = len(net.transitions)
    return stats


def grade(test_dirs, forced_grade=False, metrics_used=DEFAULT_METRICS_USED):
    '''
    :param paths:
        paths to the tests
    :return:

    grades the nets which were modified after their last grade
    '''
    for test_dir in test_dirs:
        prev_grade_info = load_grade_info(test_dir)

        given_net, given_im, given_fm, perfect_net, perfect_im, perfect_fm, log = load_test_dir(test_dir)
        given_net_filepath = os.path.join(test_dir, GIVEN_NET_FILENAME + NET_EXT)
        perfect_net_filepath = os.path.join(test_dir, PERFECT_NET_FILENAME + NET_EXT)

        # net stats
        stats = {}
        stats['net_stats'] = get_net_stats(given_net)
        add_data_to_grade_info(test_dir, 'given_net', stats)

        stats['net_stats'] = get_net_stats(perfect_net)
        add_data_to_grade_info(test_dir, 'perfect_net', stats)

        # log stats
        stats = {}
        stats['log_stats'] = {}
        stats['log_stats']['traces_cnt'] = len(log)
        add_data_to_grade_info(test_dir, 'log', stats)

        stats = {}

        repaired_dir_path = os.path.join(test_dir, REPAIRED_NETS_DIR_NAME)
        for repaired_net_filename in os.listdir(repaired_dir_path):
            repair_method_name, ext = os.path.splitext(repaired_net_filename)
            repaired_net_filepath = os.path.join(repaired_dir_path, repaired_net_filename)

            if ext != NET_EXT:
                continue
            print(f'=== Grading {repair_method_name} ===')

            # check time
            try:  # i'm sooo bad
                prev_grade_time = prev_grade_info[repair_method_name]['grader_data']['grade_time']
            except KeyError:
                prev_grade_time = 0
            files = [os.path.join(test_dir, GIVEN_NET_FILENAME + NET_EXT),
                     os.path.join(test_dir, PERFECT_NET_FILENAME + NET_EXT),
                     os.path.join(repaired_dir_path, repaired_net_filename)]
            cur_grade_time = 0
            for filepath in files:
                cur_grade_time = max(cur_grade_time, int(os.path.getmtime(filepath) * 10000000))
            if cur_grade_time == prev_grade_time and not forced_grade:
                print('Grade info is up-to-date')
                continue

            stats = {}
            rep_net, rep_im, rep_fm = pnml_importer.apply(os.path.join(repaired_dir_path, repaired_net_filename))

            # fitness (token-based replay)
            if Metrics.FITNESS in metrics_used:
                print('Calculating fitness...')
                fitness = log_fitness(log, rep_net, rep_im, rep_fm)
                stats['fitness'] = {}
                stats['fitness']['perc_fit_traces'] = fitness['percentage_of_fitting_traces']
                stats['fitness']['avg_trace_fitness'] = fitness['average_trace_fitness']

            # footprints similarity
            if Metrics.FOOTPRINTS_SIM in metrics_used:
                print('Calculating footprints similarity...')
                stats['footprints_similarity'] = {}
                fp_similarity_to_perfect = footprints_similarity(rep_net, rep_im, rep_fm, perfect_net, perfect_im, perfect_fm)
                stats['footprints_similarity']['to_perfect'] = round(fp_similarity_to_perfect, 3)
                fp_similarity_to_given = footprints_similarity(rep_net, rep_im, rep_fm, given_net, given_im, given_fm)
                stats['footprints_similarity']['to_given'] = round(fp_similarity_to_given, 3)

            # graph edit similarity
            if Metrics.EDIT_SIM in metrics_used:
                print('Calculating graph edit similarity...')
                stats['graph_edit_similarity'] = {}
                stats['graph_edit_similarity']['to_perfect'] = round(graph_edit_similarity_prom.sim_dist_prom(repaired_net_filepath, perfect_net_filepath), 3)
                stats['graph_edit_similarity']['to_given'] = round(graph_edit_similarity_prom.sim_dist_prom(repaired_net_filepath, given_net_filepath), 3)
                stats['graph_edit_similarity']['to_perfect'] = round(graph_edit_similarity.pn_edit_similarity(rep_net, perfect_net, we=1, wn=1, ws=1), 3)
                stats['graph_edit_similarity']['to_given'] = round(graph_edit_similarity.pn_edit_similarity(rep_net, given_net, we=1, wn=1, ws=1), 3)

            # precision
            if Metrics.PRECISION in metrics_used:
                print('Calculating precision...')
                stats['precision'] = {}
                stats['precision']['precision'] = round(precision_evaluator.apply(log, rep_net, rep_im, rep_fm, variant=precision_evaluator.Variants.ALIGN_ETCONFORMANCE), 3)

            # net stats
            stats['net_stats'] = get_net_stats(rep_net)

            # timestamp
            stats['grader_data'] = {}
            stats['grader_data']['grade_time'] = cur_grade_time

            add_data_to_grade_info(test_dir, repair_method_name, stats)


def init_test_dir(test_dir):
    '''
    creates necessary folders
    '''
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)

    visualization_dir = os.path.join(test_dir, VISUALIZATION_DIR_NAME)
    if not os.path.exists(visualization_dir):
        os.makedirs(visualization_dir)

    repaired_nets_dir = os.path.join(test_dir, REPAIRED_NETS_DIR_NAME)
    if not os.path.exists(repaired_nets_dir):
        os.makedirs(repaired_nets_dir)

# TODO: написать декоратор для вызова алгоритмов починки ?


def apply_hammocks_repair(test_dirs, repair_method_name='default_hammocks_replacement', parameters=None):
    '''
    apply the hammocks replacement algorithms to the given tests with parameters
      saves the repaired net and time/stats info
      adds visualization for presented nets
    '''
    for test_dir in test_dirs:
        given_net, given_im, given_fm, perfect_net, perfect_im, perfect_fm, log = load_test_dir(test_dir)

        rep_net, rep_init_marking, rep_final_marking, algo_stats = bad_pairs_hammocks_covering.visualize_hammocks_replacement_repair(given_net, given_im, given_fm, log,
                                                                                                                                     visualization_folder=os.path.join(test_dir, VISUALIZATION_DIR_NAME),
                                                                                                                                     parameters=parameters,
                                                                                                                                     calc_stats=True)

        pnml_exporter.apply(rep_net, rep_init_marking, os.path.join(test_dir, REPAIRED_NETS_DIR_NAME, repair_method_name + '.pnml'), final_marking=rep_final_marking)

        add_data_to_grade_info(test_dir, repair_method_name, algo_stats)

        # visualization TODO: error handling
        #   the given net
        filepath = os.path.join(test_dir, VISUALIZATION_DIR_NAME, GIVEN_NET_FILENAME + '.png')
        pn_visualizer.save(pn_visualizer.apply(given_net, given_im, given_fm), filepath)

        #   the perfect net
        net, initial_marking, final_marking = pnml_importer.apply(os.path.join(test_dir, PERFECT_NET_FILENAME + NET_EXT))
        filepath = os.path.join(test_dir, VISUALIZATION_DIR_NAME, PERFECT_NET_FILENAME + '.png')
        pn_visualizer.save(pn_visualizer.apply(net, initial_marking, final_marking), filepath)


def apply_complete_rediscovery(test_dirs, repair_method_name='complete_rediscovery'):
    for test_dir in test_dirs:
        print(f'=== {repair_method_name} for {test_dir} ===')
        given_net, given_im, given_fm, perfect_net, perfect_im, perfect_fm, log = load_test_dir(test_dir)

        wall_time, (rep_net, rep_im, rep_fm) = utils.timeit(inductive_miner.apply)(log)
        stats = {}
        stats['time'] = {
            'total_time': round(wall_time, 2)
        }

        add_data_to_grade_info(test_dir, repair_method_name, stats)
        pnml_exporter.apply(rep_net, rep_im, os.path.join(test_dir, REPAIRED_NETS_DIR_NAME, repair_method_name + '.pnml'), final_marking=rep_fm)
