from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils


def make_transition(alias, net, is_hidden = False):
    t = None
    underscore = '_'.join(alias.split(' '))
    if is_hidden:
        t = PetriNet.Transition(name=f'{underscore}_hidden_t', label=None)
    else:
        t = PetriNet.Transition(name=f'{underscore}_t', label=alias)

    net.transitions.add(t)
    return t


def create_net():

    net = PetriNet("my_petri_net")

    # places
    start = PetriNet.Place("start")
    net.places.add(start)

    plcs = [None]
    for i in range(1, 17):
        plcs.append(PetriNet.Place(f"p{i}"))
        net.places.add(plcs[i])

    end = PetriNet.Place("end")
    net.places.add(end)

    # transitions
    transitions = {}
    transitions['take device'] = make_transition('take device', net)
    transitions['inspect'] = inspect_t = make_transition('inspect', net)
    transitions['add to the db'] = add_to_db_t = make_transition('add to the db', net)
    transitions['start repair'] = start_rep_t = make_transition('start repair', net)
    transitions['order parts'] = make_transition('order parts', net)
    transitions['1st vendor'] = make_transition('1st vendor', net)
    transitions['2nd vendor'] = make_transition('2nd vendor', net)
    transitions['complete repair'] = make_transition('complete repair', net)
    transitions['test repair'] = make_transition('test repair', net)
    transitions['repair finished'] = make_transition('repair finished', net)
    transitions['inform client'] = make_transition('inform client', net)
    transitions['client came'] = make_transition('client came', net)
    transitions['client didnt come'] = make_transition('client didnt come', net)
    transitions['troubles with client'] = make_transition('troubles with client', net)
    transitions['received payment'] = make_transition('received payment', net)
    transitions['court'] = make_transition('court', net)
    transitions['sell device'] = make_transition('sell device', net)

    hidden_transitions = {}
    hidden_transitions['admit helplessness'] = make_transition('admit helplessness', net, is_hidden=True)
    hidden_transitions['no 1st vendor'] = make_transition('no 1st vendor', net, is_hidden=True)
    hidden_transitions['no 2nd vendor'] = make_transition('no 2nd vendor', net, is_hidden=True)

    # arcs
    petri_utils.add_arc_from_to(start, transitions['take device'], net)

    petri_utils.add_arc_from_to(plcs[1], transitions['inspect'], net)

    petri_utils.add_arc_from_to(plcs[2], transitions['start repair'], net)
    petri_utils.add_arc_from_to(plcs[2], hidden_transitions['admit helplessness'], net)

    petri_utils.add_arc_from_to(plcs[3], transitions['court'], net)

    petri_utils.add_arc_from_to(plcs[4], transitions['add to the db'], net)

    petri_utils.add_arc_from_to(plcs[5], transitions['repair finished'], net)

    petri_utils.add_arc_from_to(plcs[6], transitions['order parts'], net)
    petri_utils.add_arc_from_to(plcs[6], transitions['complete repair'], net)

    petri_utils.add_arc_from_to(plcs[7], transitions['1st vendor'], net)
    petri_utils.add_arc_from_to(plcs[7], hidden_transitions['no 1st vendor'], net)

    petri_utils.add_arc_from_to(plcs[8], transitions['2nd vendor'], net)
    petri_utils.add_arc_from_to(plcs[8], hidden_transitions['no 2nd vendor'], net)

    petri_utils.add_arc_from_to(plcs[9], transitions['test repair'], net)

    petri_utils.add_arc_from_to(plcs[10], transitions['complete repair'], net)

    petri_utils.add_arc_from_to(plcs[11], transitions['complete repair'], net)

    petri_utils.add_arc_from_to(plcs[12], transitions['repair finished'], net)

    petri_utils.add_arc_from_to(plcs[13], transitions['inform client'], net)

    petri_utils.add_arc_from_to(plcs[14], transitions['client came'], net)
    petri_utils.add_arc_from_to(plcs[14], transitions['client didnt come'], net)

    petri_utils.add_arc_from_to(plcs[15], transitions['sell device'], net)

    petri_utils.add_arc_from_to(plcs[16], transitions['troubles with client'], net)
    petri_utils.add_arc_from_to(plcs[16], transitions['received payment'], net)

    #
    petri_utils.add_arc_from_to(transitions['take device'], plcs[1], net)
    petri_utils.add_arc_from_to(transitions['take device'], plcs[4], net)

    petri_utils.add_arc_from_to(transitions['inspect'], plcs[2], net)

    petri_utils.add_arc_from_to(transitions['add to the db'], plcs[5], net)

    petri_utils.add_arc_from_to(hidden_transitions['admit helplessness'], plcs[12], net)

    petri_utils.add_arc_from_to(transitions['start repair'], plcs[6], net)

    petri_utils.add_arc_from_to(transitions['order parts'], plcs[7], net)
    petri_utils.add_arc_from_to(transitions['order parts'], plcs[8], net)

    petri_utils.add_arc_from_to(transitions['1st vendor'], plcs[10], net)

    petri_utils.add_arc_from_to(hidden_transitions['no 1st vendor'], plcs[10], net)

    petri_utils.add_arc_from_to(transitions['2nd vendor'], plcs[11], net)

    petri_utils.add_arc_from_to(hidden_transitions['no 2nd vendor'], plcs[11], net)

    petri_utils.add_arc_from_to(transitions['complete repair'], plcs[9], net)

    petri_utils.add_arc_from_to(transitions['test repair'], plcs[12], net)

    petri_utils.add_arc_from_to(transitions['repair finished'], plcs[13], net)

    petri_utils.add_arc_from_to(transitions['inform client'], plcs[14], net)

    petri_utils.add_arc_from_to(transitions['client came'], plcs[16], net)

    petri_utils.add_arc_from_to(transitions['client didnt come'], plcs[15], net)

    petri_utils.add_arc_from_to(transitions['troubles with client'], plcs[3], net)

    petri_utils.add_arc_from_to(transitions['received payment'], end, net)

    petri_utils.add_arc_from_to(transitions['sell device'], end, net)

    petri_utils.add_arc_from_to(transitions['court'], end, net)

    # # marking
    net_initial_marking = Marking()
    net_initial_marking[start] = 1
    net_final_marking = Marking()
    net_final_marking[end] = 1

    return net, net_initial_marking, net_final_marking
