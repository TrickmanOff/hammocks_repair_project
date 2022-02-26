from pm4py.objects.petri_net.obj import PetriNet, Marking


def find_transition_by_label(net, label):
    for transition in net.transitions:
        if transition.label == label:
            return transition
    return None


def _del_arc(arc, net):
    if arc is None:
        return
    if arc is None:
        return

    print('removed', arc)

    arc.source.out_arcs.remove(arc)
    arc.target.in_arcs.remove(arc)
    net.arcs.remove(arc)


def del_arc(source_name, target_name, net):
    bad_arc = None
    for arc in net.arcs:
        match_source = (source_name == arc.source.name)
        if isinstance(arc.source, PetriNet.Transition):
            match_source = match_source or (source_name == arc.source.label)
        match_target = (target_name == arc.target.name)
        if isinstance(arc.target, PetriNet.Transition):
            match_target = match_target or (target_name == arc.target.label)

        if match_source and match_target:
            bad_arc = arc

    _del_arc(bad_arc, net)


def del_trans(label, net):
    """
    delete with arcs
    """
    del_tr = None
    for trans in net.transitions:
        if trans.label == label or trans.name == label:
            del_tr = trans
            break

    if del_tr is None:
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
    del_plc = None
    for place in net.places:
        if place.name == label:
            del_plc = place
            break

    if del_plc is None:
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
        if (place.name == source_name):
            source = place
        if (place.name == target_name):
            target = place

    for trans in net.transitions:
        if (trans.label == source_name):
            source = trans
        if (trans.label == target_name):
            target = trans

    if source is None or target is None:
        return
    # print(source, target)
    arc = PetriNet.Arc(source, target, 1)
    if arc in net.arcs:
        return
    print('created', arc)
    net.arcs.add(arc)
