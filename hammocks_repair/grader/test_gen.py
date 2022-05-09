from . import grader
import hammocks_repair.examples.bad_pairs_hammocks_covering as bad_pairs_hammocks_covering
import hammocks_repair.hammocks_covering.algorithm as hammocks_covering_algo
import hammocks_repair.net_repair.hammocks_replacement.algorithm as hammocks_replacement_algo
from hammocks_repair.utils import net_helpers

from pm4py.objects.conversion.log import converter
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.obj import PetriNet
from hammocks_repair.hammocks_covering.obj import Hammock

import pm4py

from typing import Union, List
import numpy as np
import os
import shutil
import pandas as pd
import random
from copy import copy

'''
generates tests for grading
'''


def _add_noise_to_trace(trace, noise_threshold=0.05, swap_pr=1 / 3, del_pr=1 / 3, ins_pr=1 / 3,
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
            if len(trace) == 0:
                continue
            i = random.randint(0, len(trace) - 1)
            trace.pop(i)  # very slow but I think it's fine
        elif op_code < ins_pr:  # insert
            act = activities_to_insert[random.randint(0, len(activities_to_insert) - 1)]
            i = random.randint(0, len(trace))
            trace.insert(i, act)
    return trace


def add_noise_to_trace(trace, noise_threshold=0.05, swap_pr=1/3, del_pr=1/3, ins_pr=1/3,
                       activities_to_insert=None):
    '''
    trace: list of strings
    activities_to_insert: list of strings
    '''
    # the first and the last activities are left unchanged
    st_offset = 1
    end_offset = 1

    if activities_to_insert is None:
        activities_to_insert = [act for act in
                                trace]  # repetitions of activities are intentionally allowed

    mid = _add_noise_to_trace(trace[st_offset:-end_offset], noise_threshold, swap_pr, del_pr,
                              ins_pr, activities_to_insert)
    return trace[:st_offset] + mid + trace[-end_offset:]


def add_noise_to_log(log: EventLog, noise_trace_prob=0.3, noise_threshold=0.05, swap_pr=1/3, del_pr=1/3, ins_pr=1/3, activities_to_insert=None):
    print("=== Adding noise to a log ===")
    df_log = converter.apply(log, variant=converter.Variants.TO_DATA_FRAME)

    traces = df_log.groupby('case:concept:name')
    traces = [traces.get_group(trace) for trace in traces.groups]

    noised_df_log = pd.DataFrame()

    for trace in traces:
        act_seq = list(trace['concept:name'].values)

        cur_noise_threshold = noise_threshold if random.random() < noise_trace_prob else 0
        noised_act_seq = add_noise_to_trace(act_seq, cur_noise_threshold, swap_pr, del_pr, ins_pr, activities_to_insert)

        noised_df_trace = pd.concat([trace[0:1]]*len(noised_act_seq))  # could've written better?
        noised_df_trace['time:timestamp'] = pd.date_range(start='1970-01-01', periods=len(noised_act_seq), freq='5S')
        noised_df_trace['concept:name'] = noised_act_seq

        noised_df_log = pd.concat([noised_df_log, noised_df_trace])

    return pm4py.convert_to_event_log(noised_df_log)


def select_random_sublog(log, select_ratio):
    log_sz = len(log)
    perm = np.random.permutation(log_sz)

    cases_names = set()
    for i in range(int(select_ratio * log_sz)):
        cases_names.add(log[perm[i]].attributes['concept:name'])

    df_log = pm4py.convert_to_dataframe(log)
    mask = df_log['case:concept:name'].isin(cases_names)

    return pm4py.convert_to_event_log(df_log[mask])


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
            print(f"percentage_of_fitting_traces: {fitness['percentage_of_fitting_traces']}")
            print(f"avg_trace_fitness: {fitness['average_trace_fitness']}")

    return func


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
    log = xes_importer.apply(log_filepath)
    given_net_sublog = select_random_sublog(log, given_net_sublog_perc)
    # given_net_sublog = add_noise_to_log(given_net_sublog, noise_threshold=0.05)

    given_net, given_initial_marking, given_final_marking = inductive_miner.apply(given_net_sublog)

    given_log = select_random_sublog(log, given_log_sublog_perc)
    perfect_net, perfect_im, perfect_fm = pnml_importer.apply(model_filepath)

    return given_net, given_initial_marking, given_final_marking, perfect_net, perfect_im, perfect_fm, given_log


create_test_by_building_on_sublog = create_test(gen_test_by_building_on_sublog)


def gen_sample_test(case=bad_pairs_hammocks_covering.Variants.CASE1):
    given_net, given_initial_marking, given_final_marking,\
        perfect_net, perfect_initial_marking, perfect_final_marking, log = bad_pairs_hammocks_covering.get_sample_data(case)

    return given_net, given_initial_marking, given_final_marking, perfect_net, perfect_initial_marking, perfect_final_marking, log


create_sample_test = create_test(gen_sample_test)


def get_disjoint_hammocks(net: PetriNet, min_hammock_size=2) -> List[Hammock]:
    '''
    :return:
        some disjoint hammocks from the `net` that contain >= `min_hammock_size` visible transitions

    naive implementation, could be done better, but I think that's enough for testing purposes
    '''
    min_hammocks = set()
    for node in list(net.places) + list(net.transitions):
        for out_arc in node.out_arcs:
            hammock = hammocks_covering_algo.apply(net, [node, out_arc.target])
            min_hammocks.add(hammock)

    del_hammocks = []
    for ham in min_hammocks:
        if ham.size() < min_hammock_size:
            del_hammocks.append(ham)
    for ham in del_hammocks:
        min_hammocks.remove(ham)

    chosen_hammocks = []
    while len(min_hammocks) > 0:
        cur_hammock = None
        for ham in min_hammocks:
            if cur_hammock is None or len(ham.nodes) < len(cur_hammock.nodes):
                cur_hammock = ham
        chosen_hammocks.append(cur_hammock)

        del_hammocks = []
        for ham in min_hammocks:
            if len(ham.nodes & cur_hammock.nodes) > 0:
                del_hammocks.append(ham)
        for ham in del_hammocks:
            min_hammocks.remove(ham)
    return chosen_hammocks


def discover_random_subnet(log, chosen_activities_labels=None, sublog_ratio=0.3):
    df_log = converter.apply(log, variant=converter.Variants.TO_DATA_FRAME)
    if chosen_activities_labels is not None:
        df_log = df_log[df_log['concept:name'].isin(chosen_activities_labels)]

    log = converter.apply(df_log, variant=converter.Variants.TO_EVENT_LOG)
    rand_sublog = select_random_sublog(log, sublog_ratio)

    subnet, subnet_im, subnet_fm = inductive_miner.apply(rand_sublog)
    return subnet, subnet_im, subnet_fm


def worsen_net_in_hammocks(net, initial_marking, final_marking, log, min_hammock_size=3, hammocks_cnt=5, sublog_ratio=0.3):
    hammocks = get_disjoint_hammocks(net, min_hammock_size)[:hammocks_cnt]
    for ham in hammocks:
        hammock_activities_labels = {node.label for node in ham.nodes if isinstance(node, PetriNet.Transition) and node.label is not None}
        subnet, subnet_im, subnet_fm = discover_random_subnet(log, hammock_activities_labels, sublog_ratio)
        subnet_src = check_soundness.check_source_place_presence(subnet)
        subnet_sink = check_soundness.check_sink_place_presence(subnet)

        net, initial_marking, final_marking = hammocks_replacement_algo.replace_hammock(net, initial_marking, final_marking, ham, subnet, subnet_src, subnet_sink)

    net = net_helpers.enumerate_nodes_successively(net)
    return net, initial_marking, final_marking


def gen_log_for_net(net: PetriNet, initial_marking, final_marking, trace_cnt=500, max_trace_len=100) -> EventLog:
    parameters = {
        pn_playout.Variants.BASIC_PLAYOUT.value.Parameters.NO_TRACES: trace_cnt,
        pn_playout.Variants.BASIC_PLAYOUT.value.Parameters.MAX_TRACE_LENGTH: max_trace_len
    }
    sim_log = pn_playout.apply(net, initial_marking, final_marking, parameters=parameters)
    return sim_log


def gen_test_by_worsening_hammocks(model_filepath, log_filepath=None, min_hammock_size=10, hammocks_cnt=5, hammock_sublog_ratio=0.3, limit_log_for_repair=0.5):
    '''
    creates a test by rediscovering hammocks in the model on random sublogs

    :param model_filepath
        path to the model.pnml (the perfect model)
    :param log_filepath:
        path to the log.xes (log for the perfect model)
        if None a log will be generated via the model
    '''
    perfect_net, perfect_net_im, perfect_net_fm = pnml_importer.apply(model_filepath)
    log = gen_log_for_net(perfect_net, perfect_net_im, perfect_net_fm) if log_filepath is None else xes_importer.apply(log_filepath)
    log = select_random_sublog(log, limit_log_for_repair)

    # probably should limit the log for repair
    given_net, given_net_im, given_net_fm = worsen_net_in_hammocks(perfect_net, perfect_net_im, perfect_net_fm, log, min_hammock_size, hammocks_cnt, hammock_sublog_ratio)
    return given_net, given_net_im, given_net_fm, perfect_net, perfect_net_im, perfect_net_fm, log


create_test_by_worsening_hammocks = create_test(gen_test_by_worsening_hammocks)


def generate():
    model_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.pnml'
    log_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.xes'
    create_test_by_building_on_sublog('grader/tests/test1', model_path, log_path, 0.2, 0.3)

    # create_sample_test('grader/tests/sample1', case=bad_pairs_hammocks_covering.Variants.CASE1)
    # create_sample_test('grader/tests/sample2', case=bad_pairs_hammocks_covering.Variants.CASE2)
