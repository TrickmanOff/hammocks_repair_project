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

import net_repair.hammocks_replacement.algorithm as hammocks_replacement
import net_repair.naive_log_only.algorithm as naive_log_only


parameters = {
    naive_log_only.Parameters.ALIGNMENTS_REPLACE_LOGONLY_WITH: naive_log_only.ReplaceLogonlyMode.MODEL_ONLY
}

# net, _, _ = bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2, variant=net_repair_algo.Variants.NAIVE_LOG_ONLY)

# bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2, parameters=parameters, algo=naive_log_only)

bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2, parameters=parameters)

# bad_pairs_hammocks_covering.visualize_sample_repair(case=bad_pairs_hammocks_covering.Variants.CASE2,
#                                                     variant=net_repair_algo.Variants.NAIVE_LOG_ONLY)
