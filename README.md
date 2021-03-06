# What is it?

A model repair algorithm based on finding and replacing hammocks in a Petri net. The implementation uses the [PM4PY](https://github.com/pm4py) library. The algorithm itself is implemented in the [hammocks_repair](hammocks_repair) directory (code elsewhere is not guaranteed to be documented or even readable).

Theoretical explanation is to be provided.

Expecting to become a part of [PM4PY](https://github.com/pm4py) in the future.

# How to use?

```Bash
$ git clone https://github.com/TrickmanOff/hammocks_repair_project
$ pip install ./hammocks_repair_project
```

Basic example in a Python script:
```Python
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.objects.log.importer.xes import importer as xes_importer
# importing data
net, im, fm = pnml_importer.apply('data/given_net.pnml')  # net to be repaired
log = xes_importer.apply('data/log.xes')

from hammocks_repair.net_repair.hammocks_replacement import algorithm as ham_repl_algo

# applying the algorithm
rep_net, rep_im, rep_fm = ham_repl_algo.apply(net, im, fm, log)

# visualization
from pm4py.visualization.petri_net import visualizer as pn_visualizer pn_visualizer.save(pn_visualizer.apply(net, im, fm), 'initial_net.png') pn_visualizer.save(pn_visualizer.apply(rep_net, rep_im, rep_fm), 'repaired_net.png')
```

A few more interesting examples are provided [here](demo) along with data.