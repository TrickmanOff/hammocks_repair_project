import pm4py
from pm4py.objects.petri_net.utils import petri_utils

from examples import min_hammock, test_net, bad_pairs_hammocks_covering
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.conversion.log import converter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from conformance_analysis import finding_bad_pairs
from utils import net_helpers
from hammocks_covering.obj import Hammock
from hammocks_covering.variants import minimal_hammock
from pm4py.visualization.petri_net import visualizer as pn_visualizer

# min_hammock.print_min_hammock()
# min_hammock.print_min_hammock_pairs()
# bad_pairs_hammocks_covering.visualize_sample_repair(mode=1)
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri_net.importer import importer as pnml_importer

import net_repair.hammocks_replacement.algorithm as hammocks_replacement
import net_repair.naive_log_only.algorithm as naive_log_only
import numpy as np


def select_random_sublog(log, select_ratio):
    log_sz = len(log)
    perm = np.random.permutation(log_sz)

    cases_names = set()
    for i in range(int(select_ratio * log_sz)):
        cases_names.add(log[perm[i]].attributes['concept:name'])

    df_log = pm4py.convert_to_dataframe(log)
    mask = df_log['case:concept:name'].isin(cases_names)

    return pm4py.convert_to_event_log(df_log[mask])


log_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.xes'
log = xes_importer.apply(log_path)

sublog = select_random_sublog(log, 0.2)
net, initial_marking, final_marking = inductive_miner.apply(sublog)

# pn_path = '/Volumes/Samsung_T5/project/data/Process_Discovery_Contest_2020/Models/pdc_2020_1111100.pnml'
# net, initial_marking, final_marking = pnml_importer.apply(pn_path)

pn_visualizer.save(pn_visualizer.apply(net, initial_marking, final_marking), 'images/base_net.png')

check_sublog = select_random_sublog(log, 0.3)
# check_sublog = log


parameters = {
    hammocks_replacement.Parameters.PREREPAIR_VARIANT: hammocks_replacement.PrerepairVariants.NAIVE_LOG_ONLY,
    hammocks_replacement.Parameters.SUPRESS_LOGONLY_IN_ALIGNMENTS: False,
    naive_log_only.Parameters.MODIFY_ALIGNMENTS_MODE: naive_log_only.ModifyAlignments.LOG2SYNC,
}

bad_pairs_hammocks_covering.visualize_hammocks_replacement_repair(net, initial_marking, final_marking, check_sublog, parameters=parameters)
exit(0)

# net, _, _ = bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2, variant=net_repair_algo.Variants.NAIVE_LOG_ONLY)

# bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2, parameters=parameters, algo=naive_log_only)

bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2, parameters=parameters)

# bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2,
#                                                     variant=net_repair_algo.Variants.NAIVE_LOG_ONLY)
