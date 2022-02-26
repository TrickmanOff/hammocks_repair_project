from pm4py.objects.petri_net.obj import PetriNet


def get_transition_by_label(net, label):
    for transition in net.transitions:
        if transition.label == label:
            return transition
    return None
