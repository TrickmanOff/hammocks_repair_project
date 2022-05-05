import unittest

from hammocks_repair.hammocks_covering.variants import minimal_hammock
from hammocks_repair.hammocks_covering.obj import Hammock
from hammocks_repair.examples import test_net
from hammocks_repair.utils import net_helpers

Parameters = minimal_hammock.Parameters
NodeTypes = minimal_hammock.NodeTypes


def _get_nodes_by_names(net, names):
    nodes = []
    for name in names:
        plc = net_helpers.get_place_by_name(net, name)
        if plc is not None:
            nodes.append(plc)
            continue
        trans = net_helpers.find_transition(net, name)
        if trans is not None:
            nodes.append(trans)
            continue
        raise RuntimeError(f"No node with name {name} found in the net")
    return nodes


def _init_hammock(net, nodes_names, source_name, sink_name):
    true_hammock_nodes = _get_nodes_by_names(net, nodes_names)
    true_hammock_source, true_hammock_sink = _get_nodes_by_names(net, [source_name, sink_name])
    return Hammock(true_hammock_source, true_hammock_sink, true_hammock_nodes)


class MinimalHammockTest(unittest.TestCase):
    def test1(self):
        net, _, _ = test_net.create_net()
        net_src = net_helpers.get_place_by_name(net, 'start')
        net_sink = net_helpers.get_place_by_name(net, 'end')

        covered_nodes_names = ['1st_vendor_t', '2nd_vendor_t']

        # case 1
        parameters = {
            Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
        }

        true_hammock_nodes_names = ['1st_vendor_t', '2nd_vendor_t', 'order_parts_t']
        true_hammock_nodes_names += ['no_1st_vendor_hidden_t', 'no_2nd_vendor_hidden_t', 'finished_order_hidden_t']
        true_hammock_nodes_names += ['p7', 'p8', 'p10', 'p11']
        true_hammock_source_name = 'order_parts_t'
        true_hammock_sink_name = 'finished_order_hidden_t'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

        # case 2
        parameters = {
            Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
            Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        }
        true_hammock_nodes_names += ['p17', 'p6', 'no_parts_hidden_t']
        true_hammock_source_name = 'p6'
        true_hammock_sink_name = 'p17'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

        # case 3
        parameters = {
            Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.NOT_HIDDEN_TRANS_TYPE,
            Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        }

        true_hammock_nodes_names += ['start_repair_t', 'complete_repair_t']
        true_hammock_source_name = 'start_repair_t'
        true_hammock_sink_name = 'complete_repair_t'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

    def test2(self):
        '''
        covered nodes are source and sink of a hammock
        '''
        net, _, _ = test_net.create_net()
        net_src = net_helpers.get_place_by_name(net, 'start')
        net_sink = net_helpers.get_place_by_name(net, 'end')

        covered_nodes_names = ['p6', 'p17']

        parameters = {
            Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
        }

        true_hammock_nodes_names = ['1st_vendor_t', '2nd_vendor_t', 'order_parts_t']
        true_hammock_nodes_names += ['no_1st_vendor_hidden_t', 'no_2nd_vendor_hidden_t', 'finished_order_hidden_t', 'no_parts_hidden_t']
        true_hammock_nodes_names += ['p6', 'p7', 'p8', 'p10', 'p11', 'p17']
        true_hammock_source_name = 'p6'
        true_hammock_sink_name = 'p17'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

    def test3(self):
        '''
        a net with loops
        '''
        net, _, _ = test_net.create_net_loops()
        net_src = net_helpers.get_place_by_name(net, 'start')
        net_sink = net_helpers.get_place_by_name(net, 'end')

        # case 1
        covered_nodes_names = ['p1', 'p3']

        parameters = {
            Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
        }

        true_hammock_nodes_names = ['b_t', 'c_t', 'd_t', 'e_t', 'f_t'] + ['p1', 'p2', 'p3', 'p4']
        true_hammock_source_name = 'p1'
        true_hammock_sink_name = 'd_t'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)


        # case 2: sink = source
        covered_nodes_names = ['p2', 'p4']

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)
        dbg = 0


if __name__ == '__main__':
    unittest.main()
