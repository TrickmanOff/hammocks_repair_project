from pm4py.objects.petri_net.obj import PetriNet, Marking
from copy import deepcopy
from pm4py.objects.petri_net.utils import petri_utils

# TODO: get rid of the duplicates of methods from the petri_utils


def remove_node(net: PetriNet, node):
    '''
    :param node: Place or Transition
    '''
    if isinstance(node, PetriNet.Place):
        petri_utils.remove_place(net, node)
    else:
        petri_utils.remove_transition(net, node)


def get_node_by_name(net: PetriNet, name):
    node = get_place_by_name(net, name)
    if node is None:
        node = find_transition(net, name)
    return node


def get_transition_by_label(net: PetriNet, label):
    '''
    :return: the first matching transition for the `label`
    '''
    for transition in net.transitions:
        if transition.label == label:
            return transition
    return None


def find_transition(net: PetriNet, label_or_name):
    by_label = get_transition_by_label(net, label_or_name)
    if by_label is not None:
        return by_label
    return petri_utils.get_transition_by_name(net, label_or_name)


def get_place_by_name(net: PetriNet, name):
    for place in net.places:
        if place.name == name:
            return place


def find_arc(source_name, target_name, net):
    for arc in net.arcs:
        match_source = (source_name == arc.source.name)
        if isinstance(arc.source, PetriNet.Transition):
            match_source = match_source or (source_name == arc.source.label)
        match_target = (target_name == arc.target.name)
        if isinstance(arc.target, PetriNet.Transition):
            match_target = match_target or (target_name == arc.target.label)

        if match_source and match_target:
            return arc
    return None


def remove_arc(source_name, target_name, net):
    bad_arc = find_arc(source_name, target_name, net)
    petri_utils.remove_arc(net, bad_arc)


def del_trans(label, net):
    """
    delete with arcs
    """
    del_tr = find_transition(net, label)

    if del_tr is None:
        print(f'trans "{label}" not found')
        return

    # print('delete', del_tr)
    return petri_utils.remove_transition(net, del_tr)


def del_place(label, net):
    """
    delete with arcs
    """
    del_plc = get_place_by_name(net, label)

    if del_plc is None:
        print(f'place "{label}" not found')
        return
    # print('delete', del_plc)
    return petri_utils.remove_place(net, del_plc)


def create_arc(source_name, target_name, net):
    source = None
    target = None

    for place in net.places:
        if place.name == source_name:
            source = place
        if place.name == target_name:
            target = place

    for trans in net.transitions:
        if trans.label == source_name:
            source = trans
        if trans.label == target_name:
            target = trans

    if source is None or target is None:
        return
    # print(source, target)
    arc = PetriNet.Arc(source, target, 1)
    if arc in net.arcs:
        return

    source.out_arcs.add(arc)
    target.in_arcs.add(arc)
    net.arcs.add(arc)

    # print('created', arc)


def add_transition(alias, net, is_hidden=False):
    underscore = '_'.join(alias.split(' '))
    if is_hidden:
        t = PetriNet.Transition(name=f'{underscore}_hidden_t', label=None)
    else:
        t = PetriNet.Transition(name=f'{underscore}_t', label=alias)

    net.transitions.add(t)
    return t


def deepcopy_net(net, initial_marking, final_marking):
    net_copy = deepcopy(net)
    initial_marking_copy = Marking()
    for plc, cnt in initial_marking.items():
        initial_marking_copy[get_place_by_name(net_copy, plc.name)] = cnt

    final_marking_copy = Marking()
    for plc, cnt in final_marking.items():
        final_marking_copy[get_place_by_name(net_copy, plc.name)] = cnt

    return net_copy, initial_marking_copy, final_marking_copy


def enumerate_nodes_successively(net):
    for i, place in enumerate(net.places):
        place.name = 'p_' + str(i + 1)
    for i, trans in enumerate(net.transitions):
        trans.name = 't_' + str(i + 1)

    return net
