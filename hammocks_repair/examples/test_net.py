from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from hammocks_repair.utils.net_helpers import add_transition
from hammocks_repair.utils import net_helpers
from enum import Enum
from pm4py.util import exec_utils


def create_net_loops():
    net = PetriNet("my_petri_net_loops")

    # places
    start = PetriNet.Place("start")
    net.places.add(start)

    plcs = [None]
    for i in range(1, 4):
        plcs.append(PetriNet.Place(f"p{i}"))
        net.places.add(plcs[i])

    end = PetriNet.Place("end")
    net.places.add(end)

    # transitions
    transitions = {}
    transitions['b'] = add_transition('b', net)
    transitions['c'] = add_transition('c', net)
    transitions['d'] = add_transition('d', net)

    hidden_transitions = {}
    hidden_transitions['a'] = add_transition('a', net, is_hidden=True)

    # arcs
    petri_utils.add_arc_from_to(start, hidden_transitions['a'], net)
    petri_utils.add_arc_from_to(hidden_transitions['a'], plcs[1], net)
    petri_utils.add_arc_from_to(plcs[1], transitions['b'], net)
    petri_utils.add_arc_from_to(transitions['b'], plcs[1], net)
    petri_utils.add_arc_from_to(plcs[1], transitions['c'], net)
    petri_utils.add_arc_from_to(transitions['c'], plcs[2], net)
    petri_utils.add_arc_from_to(plcs[2], transitions['c'], net)
    petri_utils.add_arc_from_to(transitions['c'], plcs[3], net)
    petri_utils.add_arc_from_to(plcs[3], transitions['d'], net)
    petri_utils.add_arc_from_to(transitions['d'], plcs[3], net)
    petri_utils.add_arc_from_to(transitions['d'], end, net)

    # marking
    net_initial_marking = Marking()
    net_initial_marking[start] = 1
    net_final_marking = Marking()
    net_final_marking[end] = 1

    return net, net_initial_marking, net_final_marking


def create_net():
    net = PetriNet("my_petri_net")

    # places
    start = PetriNet.Place("start")
    net.places.add(start)

    plcs = [None]
    for i in range(1, 18):
        plcs.append(PetriNet.Place(f"p{i}"))
        net.places.add(plcs[i])

    end = PetriNet.Place("end")
    net.places.add(end)

    # transitions
    transitions = {}
    transitions['take device'] = add_transition('take device', net)
    transitions['inspect'] = inspect_t = add_transition('inspect', net)
    transitions['add to the db'] = add_to_db_t = add_transition('add to the db', net)
    transitions['start repair'] = start_rep_t = add_transition('start repair', net)
    transitions['order parts'] = add_transition('order parts', net)
    transitions['1st vendor'] = add_transition('1st vendor', net)
    transitions['2nd vendor'] = add_transition('2nd vendor', net)
    transitions['complete repair'] = add_transition('complete repair', net)
    transitions['test repair'] = add_transition('test repair', net)
    transitions['repair finished'] = add_transition('repair finished', net)
    transitions['inform client'] = add_transition('inform client', net)
    transitions['client came'] = add_transition('client came', net)
    transitions['client didnt come'] = add_transition('client didnt come', net)
    transitions['troubles with client'] = add_transition('troubles with client', net)
    transitions['received payment'] = add_transition('received payment', net)
    transitions['court'] = add_transition('court', net)
    transitions['sell device'] = add_transition('sell device', net)

    hidden_transitions = {}
    hidden_transitions['admit helplessness'] = add_transition('admit helplessness', net, is_hidden=True)
    hidden_transitions['no 1st vendor'] = add_transition('no 1st vendor', net, is_hidden=True)
    hidden_transitions['no 2nd vendor'] = add_transition('no 2nd vendor', net, is_hidden=True)
    hidden_transitions['no parts'] = add_transition('no parts', net, is_hidden=True)
    hidden_transitions['finished order'] = add_transition('finished order', net, is_hidden=True)

    # arcs
    petri_utils.add_arc_from_to(start, transitions['take device'], net)

    petri_utils.add_arc_from_to(plcs[1], transitions['inspect'], net)

    petri_utils.add_arc_from_to(plcs[2], transitions['start repair'], net)
    petri_utils.add_arc_from_to(plcs[2], hidden_transitions['admit helplessness'], net)

    petri_utils.add_arc_from_to(plcs[3], transitions['court'], net)

    petri_utils.add_arc_from_to(plcs[4], transitions['add to the db'], net)

    petri_utils.add_arc_from_to(plcs[5], transitions['repair finished'], net)

    petri_utils.add_arc_from_to(plcs[6], transitions['order parts'], net)
    petri_utils.add_arc_from_to(plcs[6], hidden_transitions['no parts'], net)

    petri_utils.add_arc_from_to(plcs[7], transitions['1st vendor'], net)
    petri_utils.add_arc_from_to(plcs[7], hidden_transitions['no 1st vendor'], net)

    petri_utils.add_arc_from_to(plcs[8], transitions['2nd vendor'], net)
    petri_utils.add_arc_from_to(plcs[8], hidden_transitions['no 2nd vendor'], net)

    petri_utils.add_arc_from_to(plcs[9], transitions['test repair'], net)

    petri_utils.add_arc_from_to(plcs[10], hidden_transitions['finished order'], net)

    petri_utils.add_arc_from_to(plcs[11], hidden_transitions['finished order'], net)

    petri_utils.add_arc_from_to(plcs[12], transitions['repair finished'], net)

    petri_utils.add_arc_from_to(plcs[13], transitions['inform client'], net)

    petri_utils.add_arc_from_to(plcs[14], transitions['client came'], net)
    petri_utils.add_arc_from_to(plcs[14], transitions['client didnt come'], net)

    petri_utils.add_arc_from_to(plcs[15], transitions['sell device'], net)

    petri_utils.add_arc_from_to(plcs[16], transitions['troubles with client'], net)
    petri_utils.add_arc_from_to(plcs[16], transitions['received payment'], net)

    petri_utils.add_arc_from_to(plcs[17], transitions['complete repair'], net)
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

    petri_utils.add_arc_from_to(hidden_transitions['no parts'], plcs[17], net)

    petri_utils.add_arc_from_to(hidden_transitions['finished order'], plcs[17], net)

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


def case1():
    '''
    delete admit_helplessness

    :return
        model_net, ...,
        real_process_net, ...
    '''
    model_net, model_init_marking, model_final_marking = create_net()
    real_net, real_init_marking, real_final_marking = create_net()

    net_helpers.del_trans('admit_helplessness_hidden_t', model_net)

    return model_net, model_init_marking, model_final_marking, \
           real_net, real_init_marking, real_final_marking


def case2():
    '''
    - simpler 'troubles with client' segment
    - only one vendor
    '''

    model_net, model_init_marking, model_final_marking = create_net()
    real_net, real_init_marking, real_final_marking = create_net()
    # troubles with client
    net_helpers.del_trans('client came', model_net)
    net_helpers.del_trans('client didnt come', model_net)
    net_helpers.del_trans('sell device', model_net)
    net_helpers.del_trans('court', model_net)

    net_helpers.del_place('p15', model_net)
    net_helpers.del_place('p16', model_net)

    net_helpers.create_arc('p14', 'received payment', model_net)
    net_helpers.create_arc('p14', 'troubles with client', model_net)

    net_helpers.add_transition('call bob', model_net)
    net_helpers.create_arc('p3', 'call bob', model_net)
    net_helpers.create_arc('call bob', 'end', model_net)

    # vendor
    net_helpers.del_place('p8', model_net)
    net_helpers.del_place('p11', model_net)

    net_helpers.del_trans('2nd vendor', model_net)
    net_helpers.del_trans('no_2nd_vendor_hidden_t', model_net)
    net_helpers.del_trans('no_1st_vendor_hidden_t', model_net)
    net_helpers.del_trans('no_parts_hidden_t', model_net)

    return model_net, model_init_marking, model_final_marking, \
           real_net, real_init_marking, real_final_marking


class Variants(Enum):
    CASE1 = case1
    CASE2 = case2


def get_case(variant=Variants.CASE1):
    return exec_utils.get_variant(variant)()
