from enum import Enum

from hammocks_covering.obj import Hammock
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.util import exec_utils
from hammocks_covering.variants import minimal_hammock
from typing import Optional, Dict, Any, Union
from pm4py.objects.petri_net.utils import check_soundness
from hammocks_covering.variants.minimal_hammock import NodeTypes
# from hammocks_covering.utils.utils import DSU

class Variants(Enum):
    DEFAULT_ALGO = minimal_hammock


class Parameters(Enum):
    HAMMOCK_SOURCE_NODE_TYPE = minimal_hammock.Parameters.PARAM_SOURCE_NODE_TYPE.value
    HAMMOCK_SINK_NODE_TYPE = minimal_hammock.Parameters.PARAM_SINK_NODE_TYPE.value


def apply(net: PetriNet, covered_nodes, as_graph=False, parameters: Optional[Dict[Any, Any]] = None, variant: Variants = Variants.DEFAULT_ALGO):
    # разделение на covered_nodes граф или просто мн-во вершин
    if not check_soundness.check_wfnet(net):
        raise Exception("Trying to apply hammocks covering search on a Petri Net that is not a WF-net")

    net_source = check_soundness.check_source_place_presence(net)
    net_sink = check_soundness.check_sink_place_presence(net)

    if as_graph:
        pass
    else:
        return apply_to_set(net, net_source, net_sink, covered_nodes, parameters, variant)


def apply_to_set(net: PetriNet, net_source, net_sink, covered_nodes, parameters: Parameters = None, variant: Variants = Variants.DEFAULT_ALGO):
    return exec_utils.get_variant(variant).apply(covered_nodes, net_source, net_sink, parameters)



def apply_to_graph(net: PetriNet, net_source, net_sink, covered_nodes, parameters: Parameters = None, variant: Variants = Variants.DEFAULT_ALGO):
    pass