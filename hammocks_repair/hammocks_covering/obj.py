from pm4py.objects.petri_net.obj import PetriNet


class Hammock(object):
    def __init__(self, source=None, sink=None, nodes=None):
        '''
        nodes contain both source and sink
        '''
        self.source = source
        self.sink = sink
        self.nodes = None if nodes is None else frozenset(nodes)

    def __eq__(self, other):
        return self.source == other.source and self.sink == other.sink and self.nodes == other.nodes

    def __hash__(self):
        return hash(self.source) + hash(self.sink) + hash(self.nodes)  # bad hash

    def size(self):
        cnt = 0
        for node in self.nodes:
            if isinstance(node, PetriNet.Transition) and node.label is not None:
                cnt += 1
        return cnt