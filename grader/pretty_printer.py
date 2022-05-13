import pandas as pd

import os
from tabulate import tabulate

from grader import grader


def pretty_print(dir, out_file):
    subdirs = [subdir for subdir in os.listdir(dir) if not subdir.startswith('.') and os.access(dir, os.R_OK)]
    subdirs.sort()

    rows = []
    repair_methods = ['given_net', 'default_hammocks_replacement', 'complete_rediscovery']

    for subdir in subdirs:
        grade_info = grader.load_grade_info(os.path.join(dir, subdir))

        for method in repair_methods:
            row = {}
            row['name'] = subdir
            row['method'] = method

            # fitness
            row['fit_avg'] = round(grade_info[method]['fitness']['avg_trace_fitness'], 3)
            row['fit_tr'] = round(grade_info[method]['fitness']['perc_fit_traces'] / 100., 3)

            # precision
            row['prec'] = round(grade_info[method]['precision']['precision'], 3)

            # similarity
            row['sim'] = None
            row['sim_approx'] = None
            row['sim_f'] = None
            if 'graph_edit_similarity' in grade_info[method]:
                row['sim'] = round(grade_info[method]['graph_edit_similarity']['to_given'], 3)
            if 'graph_edit_similarity_approx' in grade_info[method]:
                row['sim_approx'] = round(grade_info[method]['graph_edit_similarity_approx']['to_given'], 3)
            if 'footprints_similarity' in grade_info[method]:
                row['sim_f'] = round(grade_info[method]['footprints_similarity']['to_given'], 3)

            # size
            row['size'] = grade_info[method]['net_stats']['places_cnt'] + \
                          grade_info[method]['net_stats']['trans_cnt']

            # time
            if method == 'default_hammocks_replacement':
                row['time'] = grade_info[method]['time']['alignments'] + \
                              grade_info[method]['time']['prerepair'] + \
                              grade_info[method]['time']['hammocks_replacement']
                row['time_align'] = grade_info[method]['time']['alignments']
                row['time_prerep'] = grade_info[method]['time']['prerepair']
                row['time_ham'] = grade_info[method]['time']['hammocks_replacement']
            elif method == 'complete_rediscovery':
                row['time'] = grade_info[method]['time']['total_time']

            rows.append(row)

        row = {'name': '------', 'method': '------'}
        rows.append(row)

    df = pd.DataFrame().from_records(rows)

    with open(out_file, 'w') as file:
        file.write(tabulate(df, headers='keys', tablefmt='psql'))
