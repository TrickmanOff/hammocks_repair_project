import unittest

from hammocks_repair.examples import test_net
from hammocks_repair.conformance_analysis import bad_pairs_selection
from hammocks_repair.utils import net_helpers


def _get_nodes_by_names(net, names):
    nodes = []
    for name in names:
        node = net_helpers.get_node_by_name(net, name)
        if node is None:
            raise RuntimeError(f"No node with name {name} found in the net")
        nodes.append(node)
    return nodes


def _conv_bad_pairs_dict(net, bad_pairs_names):
    bad_pairs = {}
    for pair_names, cnt in bad_pairs_names.items():
        pair = tuple(_get_nodes_by_names(net, pair_names))
        bad_pairs[pair] = cnt
    return bad_pairs


class BadPairsSelectionTest(unittest.TestCase):
    def test1(self):
        """
        bad pairs with start, hidden transition
        """
        net, im, fm = test_net.create_net()

        # ( (log_name, model_name), (log_label, model_label) )
        trace = [
            ((None, 'take_device_t'), ('>>', 'take device')),
            ((None, 'add_to_the_db_t'), ('add to the db', 'add to the db')),
            ((None, 'inspect_t'), ('>>', 'inspect')),
            ((None, 'admit_helplessness_hidden_t'), ('>>', None)),  # hidden transition
            ((None, 'repair_finished_t'), ('repair finished', 'repair finished')),
            ((None, 'inform_client_t'), ('inform client', 'inform client')),
            ((None, 'client_didnt_come_t'), ('>>', 'client didnt come')),
            ((None, 'sell_device_t'), ('sell device', 'sell device')),
        ]
        alignment = {
            'alignment': trace
        }
        alignments = [alignment]

        true_bad_pairs_names = {
            ('start', 'add_to_the_db_t'): 1,
            ('start', 'repair_finished_t'): 1,
            ('inform_client_t', 'sell_device_t'): 1
        }
        true_bad_pairs = _conv_bad_pairs_dict(net, true_bad_pairs_names)

        res = bad_pairs_selection.apply(net, im, fm, alignments)
        self.assertEqual(true_bad_pairs, res)

    def test2(self):
        """
        bad pairs with end (incorrect alignments actually but expected behavior from bad_pairs_selection) + hidden transitions
        """
        net, im, fm = test_net.create_net()

        # ( (log_name, model_name), (log_label, model_label) )
        trace = [
            ((None, 'take_device_t'), ('take device', 'take device')),
            ((None, 'inspect_t'), ('inspect', 'inspect')),
            ((None, 'start_repair_t'), ('>>', 'start repair')),
            ((None, 'add_to_the_db_t'), ('>>', 'add to the db')),
            ((None, 'order_parts_t'), ('order parts', 'order parts')),
            ((None, 'no_1st_vendor_hidden_t'), ('>>', None)),
            ((None, '2nd_vendor_t'), ('2nd vendor', '2nd vendor')),
            ((None, 'finished_order_hidden_t'), ('>>', None)),
            ((None, 'complete_repair_t'), ('>>', 'complete repair')),
            ((None, 'test_repair_t'), ('test repair', 'test repair')),
            ((None, 'repair_finished_t'), ('repair finished', 'repair finished')),
            ((None, 'inform_client_t'), ('inform client', 'inform client')),
            ((None, 'client_came_t'), ('>>', 'client came')),
        ]
        alignment = {
            'alignment': trace
        }
        alignments = [alignment]

        true_bad_pairs_names = {
            ('take_device_t', 'repair_finished_t'): 1,
            ('inspect_t', 'order_parts_t'): 1,
            ('order_parts_t', 'test_repair_t'): 1,
            ('2nd_vendor_t', 'test_repair_t'): 1,
            ('inform_client_t', 'end'): 1,
        }
        true_bad_pairs = _conv_bad_pairs_dict(net, true_bad_pairs_names)

        res = bad_pairs_selection.apply(net, im, fm, alignments)
        self.assertEqual(true_bad_pairs, res)


if __name__ == '__main__':
    unittest.main()
