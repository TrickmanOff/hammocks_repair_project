import pm4py
from pm4py.objects.petri_net.utils import petri_utils

from hammocks_repair.examples import min_hammock, test_net, bad_pairs_hammocks_covering
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.conversion.log import converter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from hammocks_repair.conformance_analysis import finding_bad_pairs
from hammocks_repair.utils import net_helpers
from hammocks_repair.hammocks_covering.obj import Hammock
from hammocks_repair.hammocks_covering.variants import minimal_hammock
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from hammocks_repair.visualization import net_visualize

from hammocks_repair.grader import test_gen

# min_hammock.print_min_hammock()
# min_hammock.print_min_hammock_pairs()
# bad_pairs_hammocks_covering.visualize_sample_repair(mode=1)
from pm4py.objects.petri_net.utils import check_soundness
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.petri_net.exporter import exporter as pnml_exporter

from tests import test_minimal_hammock

import hammocks_repair.net_repair.hammocks_replacement.algorithm as hammocks_replacement
import hammocks_repair.net_repair.naive_log_only.algorithm as naive_log_only
import numpy as np

from hammocks_repair.grader import grader
import tests


def grader_example():
    parameters = {
        hammocks_replacement.Parameters.PREREPAIR_VARIANT: hammocks_replacement.PrerepairVariants.NAIVE_LOG_ONLY,
        hammocks_replacement.Parameters.SUPRESS_LOGONLY_IN_ALIGNMENTS: False,
        naive_log_only.Parameters.MODIFY_ALIGNMENTS_MODE: naive_log_only.ModifyAlignments.LOG2SYNC,
    }

    test_dirs = ['/Users/trickman/PycharmProjects/hammocks_repair/grader/tests/sample2']

    grader.apply_complete_rediscovery(test_dirs)
    grader.apply_hammocks_repair(test_dirs, parameters=parameters)
    grader.grade(test_dirs, forced_grade=True)


def worsen_net_hammocks_example():
    net, im, fm = pnml_importer.apply('/Users/trickman/PycharmProjects/hammocks_repair/grader/tests/sample2/perfect_net.pnml')
    log = xes_importer.apply('/Users/trickman/PycharmProjects/hammocks_repair/grader/tests/sample2/log.xes')
    hammocks = test_gen.get_disjoint_hammocks(net, 3)

    pn_visualizer.save(net_visualize.visualize_hammocks(net, hammocks, {}), 'images/get_disjoint_hammocks.png')

    net, im, fm = test_gen.worsen_net_in_hammocks(net, im, fm, log, min_hammock_size=3, sublog_ratio=0.1)
    pn_visualizer.save(pn_visualizer.apply(net, im, fm), 'images/worsened_net.png')


def worsen_net_hammocks_example2():
    net, im, fm = pnml_importer.apply('/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6-m.pnml')
    log = xes_importer.apply('/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6.xes')
    hammocks = test_gen.get_disjoint_hammocks(net, 10)[:5]

    pn_visualizer.save(net_visualize.visualize_hammocks(net, hammocks, {}), 'images/get_disjoint_hammocks_test.png')

    net, im, fm = test_gen.worsen_net_in_hammocks(net, im, fm, log, min_hammock_size=5, hammocks_cnt=5, sublog_ratio=0.1)
    pn_visualizer.save(pn_visualizer.apply(net, im, fm), 'images/worsened_net_test.png')


tester = tests.test_minimal_hammock.MinimalHammockTest()
tester.test3()

test_dir = '/Users/trickman/PycharmProjects/hammocks_repair/grader/tests/test1-ham-worse'
model_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6-m.pnml'
log_path = '/Volumes/Samsung_T5/project/data/BPM2013benchmarks/prAm6-m.xes'

# test_gen.create_test_by_worsening_hammocks(test_dir, model_path, log_path, calc_fitness=False, hammocks_cnt=5)

# parameters = {
#     hammocks_replacement.Parameters.PREREPAIR_VARIANT: hammocks_replacement.PrerepairVariants.NAIVE_LOG_ONLY,
#     hammocks_replacement.Parameters.SUPRESS_LOGONLY_IN_ALIGNMENTS: False,
#     naive_log_only.Parameters.MODIFY_ALIGNMENTS_MODE: naive_log_only.ModifyAlignments.LOG2SYNC,
#     hammocks_replacement.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: hammocks_replacement.NodeTypes.PLACE_TYPE | hammocks_replacement.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
#     hammocks_replacement.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: hammocks_replacement.NodeTypes.PLACE_TYPE | hammocks_replacement.NodeTypes.NOT_HIDDEN_TRANS_TYPE,
# }
#
# test_dirs = [test_dir]
# grader.apply_hammocks_repair(test_dirs, parameters=parameters)
# grader.apply_complete_rediscovery(test_dirs)
# grader.grade(test_dirs, metrics_used=[grader.Metrics.FITNESS, grader.Metrics.PRECISION, grader.Metrics.EDIT_SIM])
