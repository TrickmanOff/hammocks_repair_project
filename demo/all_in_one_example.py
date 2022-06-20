from hammocks_repair_project.grader import grader

# specifying the testing directories in which 'log.xes' and 'given_net.pnml' must be present
test_dirs = ['data']

from hammocks_repair.net_repair.hammocks_replacement import algorithm as ham_repl_algo
from hammocks_repair.net_repair.naive_log_only import algorithm as naive_log_algo
NodeTypes = ham_repl_algo.NodeTypes

# specifying parameters of the algorithm
parameters = {
ham_repl_algo.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
ham_repl_algo.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
naive_log_algo.Parameters.ALIGNMENTS_MODIFICATION_MODE: naive_log_algo.AlignmentsModificationMode.LOG2SYNC,
     # to prevent alignments recalculation by modifying the alignments during the "prerepair"
     # applying the algorithm
}

# specifying necessary metrics to calculate
# (omitting EDIT_SIM as global variables in grader/metrics/graph_edit_similarity_prom.py should be edited)
metrics = set(grader.DEFAULT_METRICS_USED)
metrics.difference_update([grader.Metrics.EDIT_SIM])

# applying the hammocks replacement repair algorithm
grader.apply_hammocks_repair(test_dirs, parameters=parameters)
# applying complete rediscovery for comparison
grader.apply_complete_rediscovery(test_dirs)

# calculating metrics (stored in the grade_info.json)
grader.grade(test_dirs, metrics_used=metrics)

# print these metrics and some info in convenient format
from hammocks_repair_project.grader import pretty_printer
pretty_printer.pretty_print(test_dirs, 'results.txt')
