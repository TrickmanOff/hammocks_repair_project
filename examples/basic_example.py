# importing net and log
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.log.importer.xes import importer as xes_importer

net, im, fm = pnml_importer.apply('data/given_net.pnml')
log = xes_importer.apply('data/log.xes')

from hammocks_repair.net_repair.hammocks_replacement import algorithm as ham_repl_algo
from hammocks_repair.net_repair.naive_log_only import algorithm as naive_log_algo

NodeTypes = ham_repl_algo.NodeTypes # parameters
parameters = {
    ham_repl_algo.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
    ham_repl_algo.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
}
# applying the algorithm
rep_net, rep_im, rep_fm = ham_repl_algo.apply(net, im, fm, log, parameters=parameters)

# visualization
from pm4py.visualization.petri_net import visualizer as pn_visualizer
pn_visualizer.save(pn_visualizer.apply(net, im, fm), 'initial_net.png')
pn_visualizer.save(pn_visualizer.apply(rep_net, rep_im, rep_fm), 'repaired_net.png')
