from . import grader
import examples.bad_pairs_hammocks_covering as bad_pairs_hammocks_covering

from pm4py.objects.conversion.log import converter
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.log.obj import EventLog
import pm4py

import numpy as np
import os
import shutil
import pandas as pd
import random
from copy import copy

'''
generates tests for grading
'''


def __add_noise_to_trace(trace, noise_threshold=0.05, swap_pr=1 / 3, del_pr=1 / 3, ins_pr=1 / 3,
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


def add_noise_to_trace(trace, noise_threshold=0.05, swap_pr=1 / 3, del_pr=1 / 3, ins_pr=1 / 3,
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

    mid = __add_noise_to_trace(trace[st_offset:-end_offset], noise_threshold, swap_pr, del_pr,
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


def create_test_by_building_on_sublog(test_folder, model_filepath, log_filepath, given_net_sublog_perc=0.2, given_log_sublog_perc=0.3):
    '''
    :param test_folder:
        where to export test data
    :param model_filepath
        path to the model.pnml (the perfect model)
    :param log_filepath:
        path to the log.xes (log for the perfect model)
    :param given_net_sublog_perc:
        percentage of the log.xes to take for discovering a given net
    :param given_log_sublog_perc:
        percentage of the log.xes to take for repairing the given net
    :return:
        creates a test
    '''
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    log = xes_importer.apply(log_filepath)
    given_net_sublog = select_random_sublog(log, given_net_sublog_perc)
    # given_net_sublog = add_noise_to_log(given_net_sublog, noise_threshold=0.05)

    print("=== Mining the given net ===")
    given_net, given_initial_marking, given_final_marking = inductive_miner.apply(given_net_sublog)
    print("Mined")
    pnml_exporter.apply(given_net, given_initial_marking, os.path.join(test_folder, grader.GIVEN_NET_FILENAME + grader.NET_EXT), final_marking=given_final_marking)

    given_log = select_random_sublog(log, given_log_sublog_perc)
    xes_exporter.apply(given_log, os.path.join(test_folder, grader.LOG_FOR_REPAIR_FILENAME))

    shutil.copyfile(model_filepath, os.path.join(test_folder, grader.PERFECT_NET_FILENAME))

    print(f'Created test in the folder \'{test_folder}\'')


def create_sample_test(test_folder, case=bad_pairs_hammocks_covering.Variants.CASE1):
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    given_net, given_initial_marking, given_final_marking,\
        perfect_net, perfect_initial_marking, perfect_final_marking, log = bad_pairs_hammocks_covering.get_sample_data(case)

    pnml_exporter.apply(given_net, given_initial_marking, os.path.join(test_folder, grader.GIVEN_NET_FILENAME + grader.NET_EXT), final_marking=given_final_marking)
    xes_exporter.apply(log, os.path.join(test_folder, grader.LOG_FOR_REPAIR_FILENAME))
    pnml_exporter.apply(perfect_net, perfect_initial_marking, os.path.join(test_folder, grader.PERFECT_NET_FILENAME + grader.NET_EXT), final_marking=perfect_final_marking)
    print(f'Created test in the folder \'{test_folder}\'')


def generate():
    model_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.pnml'
    log_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.xes'
    create_test_by_building_on_sublog('grader/tests/test1', model_path, log_path, 0.2, 0.3)

    # create_sample_test('grader/tests/sample1', case=bad_pairs_hammocks_covering.Variants.CASE1)
    # create_sample_test('grader/tests/sample2', case=bad_pairs_hammocks_covering.Variants.CASE2)
