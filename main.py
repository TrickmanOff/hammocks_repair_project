from hammocks_covering.examples import min_hammock
from hammocks_covering.examples import test_net
from pm4py.algo.simulation.playout.petri_net import algorithm as pn_playout
from pm4py.objects.conversion.log import converter
from pm4py.algo.filtering.pandas.end_activities import end_activities_filter
from conformance_analysis import bad_pairs
from utils import net_helpers
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from hammocks_covering import algorithm as hammocks_covering

# min_hammock.print_min_hammock()
# min_hammock.print_min_hammock_pairs()

min_hammock.print_bad_pair_hammock()
exit(0)

net, init_marking, final_marking = test_net.create_net()


sim_log = pn_playout.apply(net, init_marking, final_marking)
df = converter.apply(sim_log, variant=converter.Variants.TO_DATA_FRAME)
filtered_log = end_activities_filter.apply(df, ['sell device', 'received payment', 'court'])


# delete the 2nd vendor  # no sense as it produces a log-only move
# net_helpers.del_place('p7', net)
# net_helpers.del_place('p10', net)
# net_helpers.del_trans('1st vendor', net)
# net_helpers.del_trans('no_1st_vendor_hidden_t', net)

net_helpers.del_trans('admit_helplessness_hidden_t', net)

# for place in net.places:
#     print(place.name)
#     print('  out:  ', end='')
#     for out_arc in place.out_arcs:
#         print(out_arc.target, end=' ')
#     print('\n  in:  ', end='')
#     for in_arc in place.in_arcs:
#         print(in_arc.source, end=' ')
#     print('')

bad_pairs = bad_pairs.find_bad_pairs(net, init_marking, final_marking, converter.apply(df, variant=converter.Variants.TO_EVENT_LOG))



# print(filtered_log[:40])
