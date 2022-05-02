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

from grader import test_gen

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

from grader import grader


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
