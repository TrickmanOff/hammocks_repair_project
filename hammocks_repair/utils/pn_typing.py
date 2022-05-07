from typing import Union

from pm4py.objects.petri_net.obj import PetriNet

NetNode = Union[PetriNet.Place, PetriNet.Transition]
