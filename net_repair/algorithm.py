from enum import Enum
from typing import Optional, Dict, Any

from pm4py.util import exec_utils
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments_algo

from net_repair.variants import hammocks_replacement, naive_log_only
from net_repair.variants.hammocks_replacement import NodeTypes
from utils import net_helpers


class Parameters(Enum):
    HAMMOCK_PERMITTED_SOURCE_NODE_TYPE = hammocks_replacement.Parameters.HAMMOCK_PERMITTED_SOURCE_NODE_TYPE.value
    HAMMOCK_PERMITTED_SINK_NODE_TYPE = hammocks_replacement.Parameters.HAMMOCK_PERMITTED_SINK_NODE_TYPE.value
    SUBPROCESS_MINER_ALGO = hammocks_replacement.Parameters.SUBPROCESS_MINER_ALGO.value
    SUBPROCESS_MINER_ALGO_VARIANT = hammocks_replacement.Parameters.SUBPROCESS_MINER_ALGO_VARIANT.value
    HAMMOCKS_REPLACEMENT_PREREPAIR_VARIANT = 'hammocks_replacement_prerepair_variant'


class Variants(Enum):
    HAMMOCKS_REPLACEMENT = hammocks_replacement
    NAIVE_LOG_ONLY = naive_log_only


'''
repair variants that change the given alignments to use them during the hammocks replacement algorithm
it allows not to find new alignments after the prerepair
'''
HAMMOCKS_REPLACEMENT_CHANGING_ALIGNMENTS_VARIANTS = {
    Variants.NAIVE_LOG_ONLY
}


DEFAULT_VARIANT = Variants.HAMMOCKS_REPLACEMENT
HAMMOCKS_REPLACEMENT_DEFAULT_PREREPAIR_VARIANT = Variants.NAIVE_LOG_ONLY


def apply_hammocks_repair(net: PetriNet, initial_marking, final_marking, log, alignments=None, parameters: Optional[Dict[Any, Any]] = None):
    if parameters is None:
        parameters = {}
    prerepair_variant = parameters.get(Parameters.HAMMOCKS_REPLACEMENT_PREREPAIR_VARIANT, HAMMOCKS_REPLACEMENT_DEFAULT_PREREPAIR_VARIANT)
    if prerepair_variant is not None:
        net, initial_marking, final_marking = exec_utils.get_variant(prerepair_variant).apply(net, initial_marking, final_marking, log,
                                                    alignments, parameters)

    if prerepair_variant not in HAMMOCKS_REPLACEMENT_CHANGING_ALIGNMENTS_VARIANTS:
        # recalculate the alignments
        pass

    return Variants.HAMMOCKS_REPLACEMENT.value().apply(net, initial_marking, final_marking, log, alignments, parameters)


def apply(net: PetriNet, initial_marking, final_marking, log, parameters: Optional[Dict[Any, Any]] = None, alignments=None,
          variant=DEFAULT_VARIANT):

    # in order not to change the initial net
    net, initial_marking, final_marking = net_helpers.deepcopy_net(net, initial_marking,
                                                                   final_marking)

    if alignments is None:
        alignments_parameters = {
                    alignments_algo.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True
                    }
        alignments = alignments_algo.apply_log(log, net, initial_marking, final_marking, parameters=alignments_parameters)

    if variant == Variants.HAMMOCKS_REPLACEMENT:
        return apply_hammocks_repair(net, initial_marking, final_marking, log, alignments, parameters)
    else:
        return exec_utils.get_variant(variant).apply(net, initial_marking, final_marking, log, alignments, parameters)
