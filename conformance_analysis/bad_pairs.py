from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
from copy import copy
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments


DEBUG = False


class MyToken:
    def __init__(self):
        self.direct_ancestors = set()  # just ancestors
        self.red_ancestors = set()    # ancestors before bad transitions


def format_alignment(alignment):
    '''
    'log': labels
    'model': (label, name)
    '''
    log_steps = [labels[0] for names, labels in alignment]
    model_steps = [(labels[1], names[1]) for names, labels in alignment]
    data = {'log' : log_steps, 'model' : model_steps}
    return data


def __find_bad_pairs(net: PetriNet, alignment, initial_marking):
    '''
    alignment for one trace
              must be formatted
    '''

    bad_pairs = {}  # pair : cnt

    marking = {}  # place -> [tokens]
    for plc in net.places:
        marking[plc] = []

    for place, cnt in initial_marking.items():
        marking[place] = [MyToken()] * cnt

    if DEBUG:
        print_my_marking(marking)

    for i in range(len(alignment['model'])):
        model_label, model_name = alignment['model'][i]
        log_label = alignment['log'][i]

        if model_label != '>>':  # fired transition
            # find transition
            fired_transition = None
            for t in net.transitions:
                if t.name == model_name:
                    fired_transition = t
                    break
            if DEBUG:
                print(f'fired transition: {fired_transition}')

            consumed_tokens = []
            # consume tokens
            for in_arc in fired_transition.in_arcs:
                in_plc = in_arc.source
                consumed_tokens.append(marking[in_plc].pop(0))

            # unite lists
            union_token = MyToken()
            for token in consumed_tokens:
                union_token.red_ancestors = set.union(union_token.red_ancestors,
                                                      token.red_ancestors)
                union_token.direct_ancestors = set.union(union_token.direct_ancestors,
                                                         token.direct_ancestors)

            if model_label is None:  # hidden transition
                # just save the condition
                pass
            elif model_label == log_label:  # sync move
                for red_ancestor in union_token.red_ancestors:  # add a pair of transitions
                    pair = (red_ancestor, fired_transition.label)
                    if DEBUG:
                        print(f'added bad pair:\t{pair}')
                    if pair in bad_pairs:
                        bad_pairs[pair] += 1
                    else:
                        bad_pairs[pair] = 1
                union_token.red_ancestors = set()
                union_token.direct_ancestors = set([fired_transition.label])
            elif log_label == '>>':  # model-only move
                union_token.red_ancestors = set.union(union_token.red_ancestors,
                                                      union_token.direct_ancestors)

            # produce tokens
            for out_arc in fired_transition.out_arcs:
                out_plc = out_arc.target
                marking[out_plc].append(copy(union_token))

            if DEBUG:
                print_my_marking(marking)
        else:  # log-only move
            pass

    return bad_pairs


def find_bad_pairs(net: PetriNet, initial_marking, final_marking, log):
    '''
    applying alignments
    '''

    parameters = {
        alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_ALIGNMENT_RESULT_IS_SYNC_PROD_AWARE: True}
    aligned_traces = alignments.apply_log(log, net, initial_marking,
                                          final_marking, parameters=parameters)

    bad_pairs = {}

    for aligned_trace in aligned_traces:
        alignment = format_alignment(aligned_trace['alignment'])
        cur_bad_pairs = __find_bad_pairs(net, alignment, initial_marking)
        for plc, cnt in cur_bad_pairs.items():
            if plc in bad_pairs:
                bad_pairs[plc] += cnt
            else:
                bad_pairs[plc] = cnt

    return bad_pairs
