from examples import min_hammock, test_net, bad_pairs_hammocks_covering
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.conversion.log import converter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from conformance_analysis import finding_bad_pairs
from utils import net_helpers

# min_hammock.print_min_hammock()
# min_hammock.print_min_hammock_pairs()
bad_pairs_hammocks_covering.print_bad_pairs_hammock()
