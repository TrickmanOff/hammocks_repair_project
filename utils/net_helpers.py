from pm4py.objects.petri_net.obj import PetriNet, Marking
from copy import deepcopy
from pm4py.objects.petri_net.utils import petri_utils

# TODO: get rid of the duplicates of methods from the petri_utils


def find_transition(label, net):
    for transition in net.transitions:
        if transition.label == label or transition.name == label:
            return transition
    return None


def find_place(label, net):
    for place in net.places:
        if place.name == label:
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


def _del_arc(arc, net):
    if arc is None:
        return

    print('removed', arc)

    arc.source.out_arcs.remove(arc)
    arc.target.in_arcs.remove(arc)
    net.arcs.remove(arc)


def del_arc(source_name, target_name, net):
    bad_arc = find_arc(source_name, target_name, net)
    _del_arc(bad_arc, net)


def del_trans(label, net):
    """
    delete with arcs
    """
    del_tr = find_transition(label, net)

    if del_tr is None:
        print(f'trans "{label}" not found')
        return
    print('delete', del_tr)
    net.transitions.remove(del_tr)
    arcs_to_del = list(del_tr.in_arcs) + list(del_tr.out_arcs)
    for arc in arcs_to_del:
        _del_arc(arc, net)


def del_place(label, net):
    """
    delete with arcs
    """
    del_plc = find_place(label, net)

    if del_plc is None:
        print(f'place "{label}" not found')
        return
    print('delete', del_plc)
    net.places.remove(del_plc)
    arcs_to_del = list(del_plc.in_arcs) + list(del_plc.out_arcs)
    for arc in arcs_to_del:
        _del_arc(arc, net)


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

    print('created', arc)


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
        initial_marking_copy[find_place(plc.name, net_copy)] = cnt

    final_marking_copy = Marking()
    for plc, cnt in final_marking.items():
        final_marking_copy[find_place(plc.name, net_copy)] = cnt

    return net_copy, initial_marking_copy, final_marking_copy
