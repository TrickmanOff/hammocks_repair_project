from hammocks_repair.hammocks_covering.obj import Hammock
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.visualization.petri_net.common import visualize
from copy import copy
from copy import deepcopy

HAMMOCK_SOURCE_COLOR = '0.482 0.214 0.878'
HAMMOCK_SINK_COLOR = '#96a0f3'
HAMMOCK_OTHER_COLOR = '#abe6c3'
COVERED_COLOR = '#f497b8'
DEFAULT_NODES_COLOR = '#a8f7bf'


def get_label(obj, default_label=None):
    if isinstance(obj, PetriNet.Place):
        return obj.name if default_label is None else default_label
    else:
        if obj.label is None:
            return ""
        else:
            return obj.label


def paint_nodes(nodes_set, color=DEFAULT_NODES_COLOR, decorations=None):
    '''
    :return: decorations for the visualizer
    '''
    if decorations is None:
        decorations = {}
    for node in nodes_set:
        decorations[node] = {'color': color,
                             'label': get_label(node, "")}
    return decorations


def visualize_hammocks(net, hammocks, covered_set):
    '''
    highlights each hammock with its source and sink
    paint all nodes from the covered_set to red
    '''
    decorations = {}
    for hammock in hammocks:
        decorations[hammock.source] = {'color': HAMMOCK_SOURCE_COLOR,
                                       'label': get_label(hammock.source, 'hammock source')}
        decorations[hammock.sink] = {'color': HAMMOCK_SINK_COLOR,
                                     'label': get_label(hammock.sink, 'hammock sink')}

        decorations = paint_nodes(hammock.nodes.difference({hammock.source, hammock.sink}),
                                  color=HAMMOCK_OTHER_COLOR, decorations=decorations)
        decorations = paint_nodes(covered_set,
                                  color=COVERED_COLOR, decorations=decorations)
    return visualize.apply(net, initial_marking={}, final_marking={}, decorations=decorations)


def copy_marking(marking, net):
    new_marking = Marking()
    for pl in marking:
        for new_net_pl in net.places:
            if pl.name == new_net_pl.name:
                new_marking[new_net_pl] = marking[pl]
    return new_marking


def visualize_pairs(bad_segs_pairs, net, initial_marking, final_marking):
    custom_net = deepcopy(net)
    init_marking = copy_marking(initial_marking, custom_net)
    final_marking = copy_marking(final_marking, custom_net)
    """
    transition: {'color': ***, 'label': ***}
    """
    nodes_map = {}
    for trans in custom_net.transitions:
        nodes_map[trans.name] = trans
    for place in custom_net.places:
        nodes_map[place.name] = place

    decorations = {}
    i = 0
    tot_pairs_cnt = sum([cnt for pair_name, cnt in bad_segs_pairs.items()])

    for pair, cnt in bad_segs_pairs.items():
        st_name, end_name = pair[0].name, pair[1].name
        st, end = nodes_map[st_name], nodes_map[end_name]
        i += 1

        # print(f'{st} -> {end}')
        if type(st) is type(end):
            if isinstance(st, PetriNet.Place):
                p = PetriNet.Transition(f'pair{i}')
            else:
                p = PetriNet.Place(f'pair{i}')
            custom_net.places.add(p)
            arc1 = PetriNet.Arc(st, p, 1)
            arc2 = PetriNet.Arc(p, end, 1)
            custom_net.arcs.add(arc1)
            custom_net.arcs.add(arc2)
            decorations[arc1] = {'color': f'0.000 {0.5 + cnt / (2 * tot_pairs_cnt)} 1.000'}
            decorations[arc2] = {'color': f'0.000 {0.5 + cnt / (2 * tot_pairs_cnt)} 1.000'}
            decorations[p] = {'color': f'0.000 {0.5 + cnt / (2 * tot_pairs_cnt)} 1.000',
                              'label': ''}
        else:
            arc = PetriNet.Arc(st, end, 1)
            decorations[arc] = {'color': f'0.000 {0.5 + cnt / (2 * tot_pairs_cnt)} 1.000'}
            custom_net.arcs.add(arc)

    return visualize.apply(custom_net, init_marking, final_marking, decorations=decorations)
