import unittest

from pm4py import fitness_alignments
from pm4py.objects.petri_net.utils import check_soundness

from hammocks_repair.grader import test_gen
from hammocks_repair.net_repair.hammocks_replacement import algorithm as hammocks_replacement_algo
from hammocks_repair.net_repair.naive_log_only import algorithm as naive_log_only_algo

NodeTypes = hammocks_replacement_algo.NodeTypes
Parameters = hammocks_replacement_algo.Parameters


class HammocksReplacementRepairTest(unittest.TestCase):
    def test1(self):
        """
        just check that no exceptions are raised, the resulting net remains a WF-net and fitness is 100%
        """
        _, _, _, net, im, fm, log = test_gen.gen_sample_test(test_gen.bad_pairs_hammocks_covering.Variants.CASE2)

        parameters = {
            Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE: NodeTypes.PLACE_TYPE | NodeTypes.NOT_HIDDEN_TRANS_TYPE,
            Parameters.PREREPAIR_VARIANT: hammocks_replacement_algo.PrerepairVariants.NAIVE_LOG_ONLY,
            naive_log_only_algo.Parameters.ALIGNMENTS_MODIFICATION_MODE: naive_log_only_algo.AlignmentsModificationMode.LOG2SYNC,
        }
        rep_net, rep_im, rep_fm = hammocks_replacement_algo.apply(net, im, fm, log, parameters=parameters)

        self.assertTrue(check_soundness.check_wfnet(rep_net))
        fitness = fitness_alignments(log, rep_net, rep_im, rep_fm)
        self.assertEqual(fitness['percentage_of_fitting_traces'], 100.)

