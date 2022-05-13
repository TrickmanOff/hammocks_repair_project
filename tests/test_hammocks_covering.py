import unittest

from hammocks_repair.hammocks_covering.variants import minimal_hammock
from hammocks_repair.hammocks_covering import algorithm as hammocks_covering_algo
from hammocks_repair.hammocks_covering.obj import Hammock
from examples import test_net
from utils import net_helpers

NodeTypes = minimal_hammock.NodeTypes


def _get_nodes_by_names(net, names):
    nodes = []
    for name in names:
        node = net_helpers.get_node_by_name(net, name)
        if node is None:
            raise RuntimeError(f"No node with name {name} found in the net")
        nodes.append(node)
    return nodes


def _init_hammock(net, nodes_names, source_name, sink_name):
    true_hammock_nodes = _get_nodes_by_names(net, nodes_names)
    true_hammock_source, true_hammock_sink = _get_nodes_by_names(net, [source_name, sink_name])
    return Hammock(true_hammock_source, true_hammock_sink, true_hammock_nodes)


class MinimalHammockTest(unittest.TestCase):
    def test1(self):
        """
        Testing different permitted NodeTypes for the source and sink of a hammock
        """
        net, _, _ = test_net.create_net()
        net_src = net_helpers.get_place_by_name(net, 'start')
        net_sink = net_helpers.get_place_by_name(net, 'end')

        covered_nodes_names = ['1st_vendor_t', '2nd_vendor_t']

        # case 1
        parameters = {
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
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
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
        }
        true_hammock_nodes_names += ['p17', 'p6', 'no_parts_hidden_t']
        true_hammock_source_name = 'p6'
        true_hammock_sink_name = 'p17'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

        # case 3
        parameters = {
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.NOT_HIDDEN_TRANS_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.NOT_HIDDEN_TRANS_TYPE,
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
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
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
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
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

        true_hammock_nodes_names = ['e_t', 'f_t'] + ['p2', 'p4']
        true_hammock_source_name = 'p2'
        true_hammock_sink_name = 'p2'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

    def test4(self):
        """
        hammock contains start/end places of the net
        """
        net, _, _ = test_net.create_net()
        net_src = net_helpers.get_place_by_name(net, 'start')
        net_sink = net_helpers.get_place_by_name(net, 'end')

        # case1: end place
        covered_nodes_names = ['client_came_t', 'client_didnt_come_t']

        parameters = {
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
        }

        true_hammock_nodes_names = ['client_came_t', 'troubles_with_client_t', 'received_payment_t', 'court_t', 'client_didnt_come_t', 'sell_device_t'] + ['p14', 'p15', 'p16', 'p3', 'end']
        true_hammock_source_name = 'p14'
        true_hammock_sink_name = 'end'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)

        # case 2: start place
        covered_nodes_names = ['inspect_t', 'add_to_the_db_t']

        parameters = {
            minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE,
            minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE,
        }

        true_hammock_nodes_names = ['take_device_t', 'inspect_t', 'add_to_the_db_t', 'start_repair_t', 'order_parts_t', '1st_vendor_t', '2nd_vendor_t', 'complete_repair_t', 'test_repair_t', 'repair_finished_t'] + \
                                   ['admit_helplessness_hidden_t', 'no_parts_hidden_t', 'no_1st_vendor_hidden_t', 'no_2nd_vendor_hidden_t', 'finished_order_hidden_t'] + \
                                   ['start', 'p1', 'p4', 'p5', 'p2', 'p6', 'p7', 'p8', 'p10', 'p11', 'p17', 'p9', 'p12', 'p13']
        true_hammock_source_name = 'start'
        true_hammock_sink_name = 'p13'

        true_hammock = _init_hammock(net, true_hammock_nodes_names, true_hammock_source_name, true_hammock_sink_name)

        covered_nodes = _get_nodes_by_names(net, covered_nodes_names)
        res_hammock = minimal_hammock.apply(covered_nodes, net_src, net_sink, parameters=parameters)

        self.assertEqual(true_hammock, res_hammock)


class HammocksCoveringTest(unittest.TestCase):
    def test1(self):
        net, _, _ = test_net.create_net()
        net_src = net_helpers.get_place_by_name(net, 'start')
        net_sink = net_helpers.get_place_by_name(net, 'end')

        # case 1: non-intersecting hammocks
        linked_pairs_names = [
            ('order_parts_t', '1st_vendor_t'),
            ('complete_repair_t', 'p9'),
        ]
        linked_pairs = [
            tuple(_get_nodes_by_names(net, list(names_pair))) for names_pair in linked_pairs_names
        ]

        parameters = {
            hammocks_covering_algo.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
            hammocks_covering_algo.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE | NodeTypes.HIDDEN_TRANS_TYPE,
        }

        hammocks_cnt = 2
        true_hammocks_nodes_names = [[]] * hammocks_cnt
        true_hammocks_source_name = [""] * hammocks_cnt
        true_hammocks_sink_name = [""] * hammocks_cnt
        true_hammocks_nodes_names[0] = ['order_parts_t', '1st_vendor_t', '2nd_vendor_t'] + ['no_1st_vendor_hidden_t', 'no_2nd_vendor_hidden_t', 'finished_order_hidden_t'] + ['p7', 'p8', 'p10', 'p11']
        true_hammocks_source_name[0] = 'order_parts_t'
        true_hammocks_sink_name[0] = 'finished_order_hidden_t'
        true_hammocks_nodes_names[1] = ['complete_repair_t'] + ['p9']
        true_hammocks_source_name[1] = 'complete_repair_t'
        true_hammocks_sink_name[1] = 'p9'

        true_hammocks = [_init_hammock(net, true_hammocks_nodes_names[i], true_hammocks_source_name[i], true_hammocks_sink_name[i]) for i in range(hammocks_cnt)]

        res_hammocks = hammocks_covering_algo.apply(net, linked_pairs, as_pairs=True, parameters=parameters)
        self.assertEqual(set(true_hammocks), set(res_hammocks))

        # case 2: intersecting hammocks
        linked_pairs_names = [
            ('order_parts_t', '1st_vendor_t'),
            ('complete_repair_t', 'p9'),
        ]
        linked_pairs = [
            tuple(_get_nodes_by_names(net, list(names_pair))) for names_pair in linked_pairs_names
        ]

        parameters = {
            hammocks_covering_algo.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE: NodeTypes.PLACE_TYPE,
            hammocks_covering_algo.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE,
        }

        hammocks_cnt = 1
        true_hammocks_nodes_names.pop(1)
        true_hammocks_source_name.pop(1)
        true_hammocks_sink_name.pop(1)
        true_hammocks_nodes_names[0] += ['complete_repair_t'] + ['no_parts_hidden_t'] + ['p6', 'p9', 'p17']
        true_hammocks_source_name[0] = 'p6'
        true_hammocks_sink_name[0] = 'p9'
        true_hammocks = [_init_hammock(net, true_hammocks_nodes_names[i], true_hammocks_source_name[i], true_hammocks_sink_name[i]) for i in range(hammocks_cnt)]

        res_hammocks = hammocks_covering_algo.apply(net, linked_pairs, as_pairs=True, parameters=parameters)
        self.assertEqual(set(true_hammocks), set(res_hammocks))


if __name__ == '__main__':
    unittest.main()
