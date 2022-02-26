from hammocks_covering.obj import Hammock
from pm4py.visualization.petri_net.common import visualize
from pm4py.objects.petri_net.obj import PetriNet

HAMMOCK_SOURCE_COLOR = '0.482 0.214 0.878'
HAMMOCK_SINK_COLOR = '#96a0f3'
HAMMOCK_OTHER_COLOR = '#abe6c3'
COVERED_COLOR = '#f497b8'


def get_label(obj, default_label):
    if isinstance(obj, PetriNet.Place):
        return default_label
    else:
        return obj.label


def visualize_hammock(net, hammock, covered_set):
    decorations = {}
    decorations[hammock.source] = {'color': HAMMOCK_SOURCE_COLOR,
                                   'label': get_label(hammock.source, 'hammock source')}
    decorations[hammock.sink] = {'color': HAMMOCK_SINK_COLOR,
                                 'label': get_label(hammock.sink, 'hammock sink')}
    for node in hammock.nodes:
        if node != hammock.source and node != hammock.sink:
            decorations[node] = {'color': HAMMOCK_OTHER_COLOR,
                                 'label': get_label(node, '')}
    for node in covered_set:
        decorations[node] = {'color': COVERED_COLOR,
                             'label': get_label(node, '')}
    return visualize.apply(net, initial_marking={}, final_marking={}, decorations=decorations)
