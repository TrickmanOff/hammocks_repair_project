class Hammock(object):

    def __init__(self, source=None, sink=None, nodes=None):
        '''
        nodes contain both source and sink
        '''
        self.source = source
        self.sink = sink
        self.nodes = nodes
