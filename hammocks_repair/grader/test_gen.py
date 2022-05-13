from . import grader
import hammocks_repair.examples.bad_pairs_hammocks_covering as bad_pairs_hammocks_covering
import hammocks_repair.hammocks_covering.algorithm as hammocks_covering_algo
import hammocks_repair.net_repair.hammocks_replacement.algorithm as hammocks_replacement_algo
from hammocks_repair.utils import net_helpers

from pm4py.util import exec_utils
from pm4py.objects.conversion.log import converter
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri_net.utils import check_soundness, petri_utils
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.petri_net.common import visualize

from hammocks_repair.hammocks_covering.obj import Hammock
from hammocks_repair.visualization import net_visualize

NodeTypes = hammocks_covering_algo.NodeTypes

import pm4py

from typing import Union, List, Dict, Tuple, Set
import numpy as np
import os
import shutil
import pandas as pd
import random
from copy import copy, deepcopy
from enum import Enum

'''
generates tests for grading
'''


# decorator
def create_test(test_gen):
    def func(test_folder, *args, **kwargs):
        '''
        :param calc_fitness
            whether calculate fitness of the given_net w.r.t. the log
        '''
        calc_fitness = True
        if 'calc_fitness' in kwargs:
            calc_fitness = kwargs['calc_fitness']
            kwargs.pop('calc_fitness')

        grader.init_test_dir(test_folder)
        given_net, given_im, given_fm, \
            perfect_net, perfect_im, perfect_fm, log = test_gen(*args, **kwargs)

        pnml_exporter.apply(given_net, given_im,
                            os.path.join(test_folder, grader.GIVEN_NET_FILENAME + grader.NET_EXT),
                            final_marking=given_fm)
        pnml_exporter.apply(perfect_net, perfect_im,
                            os.path.join(test_folder, grader.PERFECT_NET_FILENAME + grader.NET_EXT),
                            final_marking=perfect_fm)
        xes_exporter.apply(log, os.path.join(test_folder, grader.LOG_FOR_REPAIR_FILENAME))
        print(f'=== Created test in the folder \'{test_folder}\' ===')

        if calc_fitness:
            fitness = grader.log_fitness(log, given_net, given_im, given_fm)
            print('Fitness info:')
            print(f"percentage_of_fitting_traces: {round(fitness['percentage_of_fitting_traces'], 3)}")
            print(f"avg_trace_fitness: {round(fitness['average_trace_fitness'], 3)}")

            stats = {'fitness': {}}
            stats['fitness']['perc_fit_traces'] = round(fitness['percentage_of_fitting_traces'], 3)
            stats['fitness']['avg_trace_fitness'] = round(fitness['average_trace_fitness'], 3)
            grader.add_data_to_grade_info(test_folder, 'given_net', stats)

    return func


def _add_noise_to_trace(trace, noise_threshold=0.05, swap_pr=1/3, del_pr=1/3, ins_pr=1/3,
                        activities_to_insert=None):
    '''
    trace: list of strings
    activities_to_insert: list of strings
    '''
    trace = copy(trace)

    if activities_to_insert is None:
        activities_to_insert = [act for act in
                                trace]  # repetitions of activities are intentionally allowed

    # normalization
    s = swap_pr + del_pr + ins_pr
    swap_pr /= s
    del_pr /= s
    ins_pr /= s

    del_pr += swap_pr
    ins_pr += del_pr
    ops_cnt = int(noise_threshold * len(trace))
    for _ in range(ops_cnt):
        op_code = random.random()
        if op_code < swap_pr:  # swap
            if len(trace) < 2:
                continue
            i = random.randint(0, len(trace) - 1)
            j = random.randint(0, len(trace) - 1)
            trace[i], trace[j] = trace[j], trace[i]
        elif op_code < del_pr:  # delete
            if len(trace) <= 1:
                continue
            i = random.randint(0, len(trace) - 1)
            trace.pop(i)  # very slow but I think it's fine
        elif op_code < ins_pr:  # insert
            act = activities_to_insert[random.randint(0, len(activities_to_insert) - 1)]
            i = random.randint(0, len(trace))
            trace.insert(i, act)
    return trace


def add_noise_to_trace(trace, noise_threshold=0.05, swap_pr=1/3, del_pr=1/3, ins_pr=1/3, activities_to_insert=None,
                       trace_st_offset=1, trace_end_offset=1):
    '''
    trace: list of strings
    activities_to_insert: list of strings
    '''
    # the first and the last activities are left unchanged
    trace_st_offset = 1
    trace_end_offset = 1

    if activities_to_insert is None:
        activities_to_insert = [act for act in
                                trace]  # repetitions of activities are intentionally allowed

    mid = _add_noise_to_trace(trace[trace_st_offset:-trace_end_offset], noise_threshold, swap_pr, del_pr,
                              ins_pr, activities_to_insert)
    return trace[:trace_st_offset] + mid + trace[-trace_end_offset:]


def _add_noise_to_log(log: EventLog, noise_trace_prob=0.3, noise_threshold=0.05, swap_pr=1 / 3, del_pr=1 / 3, ins_pr=1 / 3, activities_to_insert=None,
                      trace_st_offset=1, trace_end_offset=1):
    print("=== Adding noise to a log ===")
    df_log = converter.apply(log, variant=converter.Variants.TO_DATA_FRAME)

    traces = df_log.groupby('case:concept:name')
    traces = [traces.get_group(trace) for trace in traces.groups]

    noised_df_log = pd.DataFrame()

    for trace in traces:
        act_seq = list(trace['concept:name'].values)

        cur_noise_threshold = noise_threshold if random.random() < noise_trace_prob else 0
        noised_act_seq = add_noise_to_trace(act_seq, cur_noise_threshold, swap_pr, del_pr, ins_pr, activities_to_insert, trace_st_offset, trace_end_offset)

        noised_df_trace = pd.concat([trace[0:1]]*len(noised_act_seq))  # could've written better?
        noised_df_trace['time:timestamp'] = pd.date_range(start='1970-01-01', periods=len(noised_act_seq), freq='5S')
        noised_df_trace['concept:name'] = noised_act_seq

        noised_df_log = pd.concat([noised_df_log, noised_df_trace])

    return pm4py.convert_to_event_log(noised_df_log)


class AddNoiseWorsening:
    class Parameters(Enum):
        NOISE_TRACE_PROB = 'noise_trace_prob'
        NOISE_THRESHOLD = 'noise_threshold'
        SWAP_PROB = 'swap_pr'
        DEL_PROB = 'del_pr'
        INS_PROB = 'ins_pr'
        ACTIVITIES_TO_INSERT = 'activities_to_insert'
        TRACE_ST_OFFSET = 'trace_st_offset'
        TRACE_END_OFFSET = 'trace_end_offset'


def _extract_params_as_kwargs(parameters: Dict, Parameters):
    kwargs = {}
    for param in Parameters:
        value = exec_utils.get_param_value(param, parameters, None)
        if value is not None:
            kwargs[param.value] = value
    return kwargs


def add_noise_to_log(log: EventLog, parameters):
    kwargs = _extract_params_as_kwargs(parameters, AddNoiseWorsening.Parameters)
    return _add_noise_to_log(log, **kwargs)


class RandomSublogWorsening:
    class Parameters(Enum):
        SELECT_RATIO = 'select_ratio'


def _select_random_sublog(log, select_ratio):
    log_sz = len(log)
    perm = np.random.permutation(log_sz)

    cases_names = set()
    for i in range(int(select_ratio * log_sz)):
        cases_names.add(log[perm[i]].attributes['concept:name'])

    df_log = pm4py.convert_to_dataframe(log)
    mask = df_log['case:concept:name'].isin(cases_names)

    return pm4py.convert_to_event_log(df_log[mask])


def select_random_sublog(log, parameters):
    kwargs = _extract_params_as_kwargs(parameters, RandomSublogWorsening.Parameters)
    return _select_random_sublog(log, **kwargs)


class SwapAndDelWorsening:
    class Parameters(Enum):
        SWAP_CNT = 'swap_cnt'
        DEL_CNT = 'del_cnt'


def _swap_and_del_trans(log, swap_cnt=1, del_cnt=1):
    df_log = converter.apply(log, variant=converter.TO_DATA_FRAME)

    trans_labels = set(df_log['concept:name'].unique())
    new_label = {label: label for label in trans_labels}

    for _ in range(del_cnt):
        del_label = random.choice(list(trans_labels))
        trans_labels.remove(del_label)
        new_label[del_label] = None

    for _ in range(swap_cnt):
        label1, label2 = random.sample(trans_labels, 2)
        new_label[label1], new_label[label2] = new_label[label2], new_label[label1]

    filtered_rows = []
    for i, row in copy(df_log).iterrows():
        label = row['concept:name']
        if new_label[label] is None:
            continue
        row['concept:name'] = new_label[label]
        filtered_rows.append(row)
    filtered_df_log = pd.DataFrame(filtered_rows)

    return converter.apply(filtered_df_log, variant=converter.TO_EVENT_LOG)


def swap_and_del_trans(log, parameters):
    kwargs = _extract_params_as_kwargs(parameters, SwapAndDelWorsening.Parameters)
    return _swap_and_del_trans(log, **kwargs)


class WorseningVariants(Enum):
    ADD_NOISE = AddNoiseWorsening
    RANDOM_SUBLOG = RandomSublogWorsening
    SWAP_AND_DEL = SwapAndDelWorsening


def worsen_net(net, initial_marking, final_marking, variant: WorseningVariants, log=None, parameters=None) -> Tuple[PetriNet, Marking, Marking]:
    if log is None:
        trace_cnt = min(500, 2*len(net.transitions))
        max_trace_length = min(1000, 10 * len(net.transitions))

        log = gen_log_for_net(net, initial_marking, final_marking, trace_cnt, max_trace_length)

    if variant == WorseningVariants.ADD_NOISE:
        worsened_log = add_noise_to_log(log, parameters)
    elif variant == WorseningVariants.RANDOM_SUBLOG:
        worsened_log = select_random_sublog(log, parameters)
    elif variant == WorseningVariants.SWAP_AND_DEL:
        worsened_log = swap_and_del_trans(log, parameters)

    res_net, res_net_im, res_net_fm = inductive_miner.apply(worsened_log)
    return res_net, res_net_im, res_net_fm


def _nodes_on_dist(node, dist) -> Set[Union[PetriNet.Place, PetriNet.Transition]]:
    cur_level = [node]
    used = {node}
    for i in range(dist):
        next_level = []
        for v in cur_level:
            for u in [in_arc.source for in_arc in v.in_arcs] + [out_arc.target for out_arc in v.out_arcs]:
                if u in used:
                    continue
                used.add(u)
                next_level.append(u)
        cur_level = next_level
    return used


def get_disjoint_hammocks(net: PetriNet, min_hammock_size=2, start_end_offset=2, hammocks_dist=2) -> List[Hammock]:
    '''
    start_end_offset
        How many levels of nodes from start/end nodes of the net should not be included to hammocks
    hammock_dist
        Distance between hammocks

    :return:
        some disjoint hammocks from the `net` that contain >= `min_hammock_size` visible transitions

    naive implementation, could be done better, but I think that's enough for testing purposes
    '''
    if not check_soundness.check_wfnet(net):
        raise RuntimeError("Not a WF-net")
    net_src = check_soundness.check_source_place_presence(net)
    net_sink = check_soundness.check_sink_place_presence(net)

    blocked_nodes = _nodes_on_dist(net_src, start_end_offset)
    blocked_nodes.update(_nodes_on_dist(net_sink, start_end_offset))

    min_hammock_parameters = {
        hammocks_covering_algo.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        hammocks_covering_algo.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
    }

    min_hammocks = set()
    for node in list(net.places) + list(net.transitions):
        for out_arc in node.out_arcs:
            hammock = hammocks_covering_algo.apply(net, [node, out_arc.target])
            while hammock.size() < min_hammock_size:
                if blocked_nodes.intersection(hammock.nodes):
                    break
                new_node = random.choice(list(hammock.source.in_arcs)).source
                hammock = hammocks_covering_algo.apply(net, [new_node, hammock.sink], parameters=min_hammock_parameters)

            if hammock.size() >= min_hammock_size:
                min_hammocks.add(hammock)

    chosen_hammocks = []
    while True:
        for ham in copy(min_hammocks):
            if len(ham.nodes & blocked_nodes) > 0:
                min_hammocks.remove(ham)

        if not min_hammocks:
            break

        cur_hammock = None
        for ham in min_hammocks:
            if cur_hammock is None or ham.size() < cur_hammock.size():
                cur_hammock = ham
        hammocks_with_min_sz = [ham for ham in min_hammocks if ham.size() == cur_hammock.size()]
        cur_hammock = random.choice(hammocks_with_min_sz)
        chosen_hammocks.append(cur_hammock)

        blocked_nodes.update(cur_hammock.nodes)
        blocked_nodes.update(_nodes_on_dist(cur_hammock.source, hammocks_dist))
        blocked_nodes.update(_nodes_on_dist(cur_hammock.sink, hammocks_dist))

    return chosen_hammocks


def _hammock_to_net(hammock: Hammock):
    net = PetriNet()

    nodes_by_names = {}
    for node in hammock.nodes:
        if isinstance(node, PetriNet.Place):
            added_node = petri_utils.add_place(net, node.name)
        else:
            added_node = petri_utils.add_transition(net, node.name, node.label)
        nodes_by_names[node.name] = added_node

    # arcs
    for node in hammock.nodes:
        for out_node in [out_arc.target for out_arc in node.out_arcs]:
            if out_node in hammock.nodes:
                petri_utils.add_arc_from_to(nodes_by_names[node.name], nodes_by_names[out_node.name], net)

    start = nodes_by_names[hammock.source.name]
    end = nodes_by_names[hammock.sink.name]

    if isinstance(start, PetriNet.Transition):
        new_start = petri_utils.add_place(net)
        petri_utils.add_arc_from_to(new_start, start, net)
        start = new_start

    if isinstance(end, PetriNet.Transition):
        new_end = petri_utils.add_place(net)
        petri_utils.add_arc_from_to(end, new_end, net)
        end = new_end

    im = Marking()
    im[start] = 1

    fm = Marking()
    fm[end] = 1

    return net, im, fm


def _label_transitions_uniquely(net):
    trans_by_label = {}
    for trans in net.transitions:
        if trans.label is None:
            continue
        if trans.label not in trans_by_label:
            trans_by_label[trans.label] = []
        trans_by_label[trans.label].append(trans)

    for transitions_with_same_label in trans_by_label.values():
        for i, trans in enumerate(transitions_with_same_label):
            if i != 0:
                trans.label = trans.label + f"#{i+1}"


def worsen_net_in_hammocks(net, initial_marking, final_marking, variant: WorseningVariants, log=None, min_hammock_size=3, hammocks_cnt=5, parameters=None,
                           visualization_dir=None):
    net, initial_marking, final_marking = net_helpers.deepcopy_net(net, initial_marking, final_marking)

    hammocks = get_disjoint_hammocks(net, min_hammock_size)[:hammocks_cnt]
    if len(hammocks) < hammocks_cnt:
        raise RuntimeError("The requested number of hammocks wasn't found in the net. Try again or try less value of hammocks_cnt")

    # hammocks visualization
    if visualization_dir is not None:
        pn_visualizer.save(net_visualize.visualize_hammocks(net, hammocks, {}, initial_marking=initial_marking, final_marking=final_marking),
                           os.path.join(visualization_dir, 'chosen_hammocks.png'))

    decorations = {}
    for i, ham in enumerate(hammocks):
        ham_net, ham_net_im, ham_net_fm = _hammock_to_net(ham)

        # visualization for debug
        if visualization_dir is not None:
            pn_visualizer.save(pn_visualizer.apply(ham_net, ham_net_im, ham_net_fm),
                               os.path.join(visualization_dir, f'hammock_net_{i+1}.png'))

        wors_ham_net, wors_ham_net_im, wors_ham_net_fm = worsen_net(ham_net, ham_net_im, ham_net_fm, variant, log, parameters)

        wors_ham_net_nodes = list(wors_ham_net.places) + list(wors_ham_net.transitions)
        decorations = net_visualize.paint_nodes(wors_ham_net_nodes, decorations=decorations, color='#f497b8')

        wors_ham_net_src = next(iter(wors_ham_net_im.keys()))
        wors_ham_net_sink = next(iter(wors_ham_net_fm.keys()))
        net, initial_marking, final_marking = hammocks_replacement_algo.replace_hammock(net, initial_marking, final_marking, ham, wors_ham_net, wors_ham_net_src, wors_ham_net_sink)

    net = net_helpers.enumerate_nodes_successively(net)
    # worsened net visualization
    if visualization_dir is not None:
        pn_visualizer.save(visualize.apply(net, initial_marking, final_marking, decorations=decorations),
                           os.path.join(visualization_dir, 'worsened_net.png'))

    return net, initial_marking, final_marking


def gen_log_for_net(net: PetriNet, initial_marking, final_marking, trace_cnt=500, max_trace_len=1000) -> EventLog:
    parameters = {
        pn_playout.Variants.BASIC_PLAYOUT.value.Parameters.NO_TRACES: trace_cnt,
        pn_playout.Variants.BASIC_PLAYOUT.value.Parameters.MAX_TRACE_LENGTH: max_trace_len
    }
    # note that it's not guaranteed that generated traces will end in the final marking if max_trace_len is limited
    sim_log = pn_playout.apply(net, initial_marking, final_marking, parameters=parameters)
    res_sim_log = EventLog()
    for trace in sim_log:
        if len(trace) != max_trace_len:  # final marking is not reached in this trace
            res_sim_log.append(trace)

    if len(res_sim_log) < trace_cnt * 0.8:
        raise RuntimeError("Too many traces didn't reach the final marking during the playout. Try to increase max_trace_len")

    return res_sim_log


def gen_test_by_worsening_hammocks(model_filepath, variant: WorseningVariants = WorseningVariants.RANDOM_SUBLOG, log_filepath=None, min_hammock_size=5, hammocks_cnt=5, parameters=None, visualization_dir=None):
    '''
    creates a test by worsening hammocks

    :param model_filepath
        path to the model.pnml (the perfect model)
    :param log_filepath:
        path to the log.xes (log for the perfect model)
        if None a log will be generated via the model
    '''
    perfect_net, perfect_net_im, perfect_net_fm = pnml_importer.apply(model_filepath)
    _label_transitions_uniquely(perfect_net)  # for simplicity

    log = None if log_filepath is None else xes_importer.apply(log_filepath)

    given_net, given_net_im, given_net_fm = worsen_net_in_hammocks(perfect_net, perfect_net_im, perfect_net_fm,
                                                                   variant, log=log,
                                                                   min_hammock_size=min_hammock_size, hammocks_cnt=hammocks_cnt, parameters=parameters,
                                                                   visualization_dir=visualization_dir)

    given_log = gen_log_for_net(perfect_net, perfect_net_im, perfect_net_fm, trace_cnt=150) if log is None else log
    return given_net, given_net_im, given_net_fm, perfect_net, perfect_net_im, perfect_net_fm, given_log


create_test_by_worsening_hammocks = create_test(gen_test_by_worsening_hammocks)


def gen_test_by_building_on_sublog(model_filepath, log_filepath, given_net_sublog_perc=0.2, given_log_sublog_perc=0.3):
    '''
    creates a test by rediscovering the model on a random sublog

    :param model_filepath
        path to the model.pnml (the perfect model)
    :param log_filepath:
        path to the log.xes (log for the perfect model)
    :param given_net_sublog_perc:
        percentage of the log.xes to take for discovering a given net
    :param given_log_sublog_perc:
        percentage of the log.xes to take for repairing the given net
    '''
    perfect_net, perfect_im, perfect_fm = pnml_importer.apply(model_filepath)
    log = gen_log_for_net(perfect_net, perfect_im, perfect_fm) if log_filepath is None else xes_importer.apply(log_filepath)

    given_net_sublog = _select_random_sublog(log, given_net_sublog_perc)
    # given_net_sublog = add_noise_to_log(given_net_sublog, noise_threshold=0.05)

    given_net, given_initial_marking, given_final_marking = inductive_miner.apply(given_net_sublog)

    given_log = _select_random_sublog(log, given_log_sublog_perc)
    return given_net, given_initial_marking, given_final_marking, perfect_net, perfect_im, perfect_fm, given_log


create_test_by_building_on_sublog = create_test(gen_test_by_building_on_sublog)


def gen_sample_test(case=bad_pairs_hammocks_covering.Variants.CASE1):
    given_net, given_initial_marking, given_final_marking,\
        perfect_net, perfect_initial_marking, perfect_final_marking, log = bad_pairs_hammocks_covering.get_sample_data(case)

    return given_net, given_initial_marking, given_final_marking, perfect_net, perfect_initial_marking, perfect_final_marking, log


create_sample_test = create_test(gen_sample_test)


def generate():
    model_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.pnml'
    log_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.xes'
    create_test_by_building_on_sublog('grader/tests/test1', model_path, log_path, 0.2, 0.3)

    # create_sample_test('grader/tests/sample1', case=bad_pairs_hammocks_covering.Variants.CASE1)
    # create_sample_test('grader/tests/sample2', case=bad_pairs_hammocks_covering.Variants.CASE2)
