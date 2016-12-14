#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: Rico Sennrich

from __future__ import division, print_function, unicode_literals
import sys
import json
import argparse
from collections import defaultdict, OrderedDict
from operator import gt, lt

# usage: python evaluate.py errors.json < scores
# by default, lower scores (closer to zero for log-prob) are better

ERROR_CATEGORIES = ['np_agreement', # wrong gender of determiner in noun phrase
                    'subj_verb_agreement', # wrong number of verb (mismatch with subject)
                    'subj_adequacy', # change number of verb if subject is "sie" (change of meaning: "she" <-> "they")
                    'polarity_particle_nicht_del', # delete negation particle "nicht"
                    'polarity_particle_kein_del', # delete negation particle ("kein" -> "ein")
                    'polarity_affix_del', # delete negation prefix "un-"
                    'polarity_particle_nicht_ins', # insert negation particle "nicht"
                    'polarity_particle_kein_ins', # insert negation particle ("kein" -> "ein")
                    'polarity_affix_ins', # insert negation prefix "un-"
                    'auxiliary', # use wrong auxiliary verb in past participle construction
                    'verb_particle', # use wrong verb particle
                    'compound', # swap first two morphemes in compounds (that do not occur in training data)
                    'transliteration'] # swap two random characters in name (that does not occur in training data)

#For frequency statistics, we define several frequency bins

FREQUENCY_BINS = OrderedDict()
# value for higher frequencies
FREQUENCY_BINS[">10k"] = []
DEFAULT_FREQUENCY = ">10k"
FREQUENCY_BINS[">5k"] = range(5001, 10001)
FREQUENCY_BINS[">2k"] = range(2001, 5001)
FREQUENCY_BINS[">1k"] = range(1001, 2001)
FREQUENCY_BINS[">500"] = range(501,1001)
FREQUENCY_BINS[">200"] = range(201,501)
FREQUENCY_BINS[">100"] = range(101,201)
FREQUENCY_BINS[">50"] = range(51,101)
FREQUENCY_BINS[">20"] = range(21,51)
FREQUENCY_BINS[">10"] = range(11,21)
FREQUENCY_BINS[">5"] = range(5,11)
FREQUENCY_BINS[">2"] = range(3,6)
FREQUENCY_BINS["2"] = [2]
FREQUENCY_BINS["1"] = [1]
FREQUENCY_BINS["0"] = [0, "0"]

# we report statistics for each distance up to 15,
# and report the rest as a single number

DISTANCE_BINS = OrderedDict()
DISTANCE_BINS["0"] = [0, "0"]
for i in range(1, 16):
  DISTANCE_BINS[str(i)] = [i]

# value for higher distances
DISTANCE_BINS[">15"] = []
DEFAULT_DISTANCE = ">15"

DISTANCE_TO_BIN = {}
for key in DISTANCE_BINS:
    for distance in DISTANCE_BINS[key]:
        DISTANCE_TO_BIN[distance] = key

FREQUENCY_TO_BIN = {}
for key in FREQUENCY_BINS:
    for freq in FREQUENCY_BINS[key]:
        FREQUENCY_TO_BIN[freq] = key

def count_errors(reference, scores, maximize, categories, verbose=False):
    """read in scores file and count number of correct decisions"""

    reference = json.load(reference)

    results = {'by_category': defaultdict(lambda: defaultdict(int)),
              'by_distance': defaultdict(lambda: defaultdict(int)),
              'by_frequency': defaultdict(lambda: defaultdict(int)),
              'by_frequency_and_distance': defaultdict(lambda: defaultdict(int))}

    if maximize:
        better = gt
    else:
        better = lt

    for sentence in reference:
        score = float(scores.readline())
        for error in sentence['errors']:
            errorscore = float(scores.readline())
            category = error['type']
            if category not in categories:
                continue
            distance = error.get('distance', None)
            if distance in DISTANCE_TO_BIN:
                distance = DISTANCE_TO_BIN[distance]
            elif distance is not None:
                distance = DEFAULT_DISTANCE
            frequency = error.get('frequency', None)
            if frequency in FREQUENCY_TO_BIN:
                frequency = FREQUENCY_TO_BIN[frequency]
            elif frequency is not None:
                frequency = DEFAULT_FREQUENCY

            results['by_category'][category]['total'] += 1
            if distance is not None:
                results['by_distance'][distance]['total'] += 1
            if frequency is not None:
                results['by_frequency'][frequency]['total'] += 1
            if frequency is not None and distance is not None:
                results['by_frequency_and_distance'][frequency, distance]['total'] += 1
            if better(score, errorscore):
                results['by_category'][category]['correct'] += 1
                if distance is not None:
                    results['by_distance'][distance]['correct'] += 1
                if frequency is not None:
                    results['by_frequency'][frequency]['correct'] += 1
                if frequency is not None and distance is not None:
                    results['by_frequency_and_distance'][frequency, distance]['correct'] += 1

            if verbose and not better(score, errorscore):
                print('error: {0}'.format(category))
                print('source: {0}'.format(sentence['source']))
                print('correct (score {0}): {1}'.format(score, sentence['reference']))
                print('error (score {0}): {1}'.format(errorscore, error['contrastive']))
                print()

    return results

def get_scores(category):
    correct = category['correct']
    total = category['total']
    if total:
        accuracy = correct/total
    else:
        accuracy = 0
    return correct, total, accuracy


def print_statistics(results):

    correct = sum([results['by_category'][category]['correct'] for category in results['by_category']])
    total = sum([results['by_category'][category]['total'] for category in results['by_category']])
    print('{0} : {1} {2} {3}'.format('total', correct, total, correct/total))


def print_statistics_by_category(results):

    for category in ERROR_CATEGORIES:
        correct, total, accuracy = get_scores(results['by_category'][category])

        if total:
            print('{0} : {1} {2} {3}'.format(category, correct, total, accuracy))

def print_statistics_by_distance(results):

    for distance in DISTANCE_BINS:
        correct, total, accuracy = get_scores(results['by_distance'][distance])

        if total:
            print('distance {0}: {1} {2} {3}'.format(distance, correct, total, accuracy))
            ##for gnuplot table
            #print('{0} {3}'.format(distance, correct, total, accuracy))

def print_statistics_by_frequency(results):

    for category in FREQUENCY_BINS:
        correct, total, accuracy = get_scores(results['by_frequency'][category])

        if total:
            print('{0} : {1} {2} {3}'.format(category, correct, total, accuracy))

def print_statistics_by_frequency_and_distance(results):

    for category in FREQUENCY_BINS:
        for distance in DISTANCE_BINS:
            correct, total, accuracy = get_scores(results['by_frequency_and_distance'][category, distance])

            if total:
                print('frequency: {0} distance: {1}: {2} {3} {4}'.format(category, distance, correct, total, accuracy))

def print_latex_table(results):
    """print LateX table as published. Different types of polarity errors are merged"""

    correct = [0]*6
    total = [0]*6

    correct[0] = results['by_category']['np_agreement']['correct']
    total[0] = results['by_category']['np_agreement']['total']

    correct[1] = results['by_category']['subj_verb_agreement']['correct']
    total[1] = results['by_category']['subj_verb_agreement']['total']

    correct[2] = results['by_category']['verb_particle']['correct']
    total[2] = results['by_category']['verb_particle']['total']

    correct[3] = sum(results['by_category'][category]['correct'] for category in ['polarity_particle_nicht_ins','polarity_particle_kein_ins','polarity_affix_ins'] )
    total[3] = sum(results['by_category'][category]['total'] for category in ['polarity_particle_nicht_ins','polarity_particle_kein_ins','polarity_affix_ins'] )


    correct[4] = sum(results['by_category'][category]['correct'] for category in ['polarity_particle_nicht_del','polarity_particle_kein_del','polarity_affix_del'] )
    total[4] = sum(results['by_category'][category]['total'] for category in ['polarity_particle_nicht_del','polarity_particle_kein_del','polarity_affix_del'] )

    correct[5] = results['by_category']['transliteration']['correct']
    total[5] = results['by_category']['transliteration']['total']

    print(' & '.join(['{0}'.format(t) for t in total]))
    print(' & '.join(['{0:.1f}'.format(c/t*100) for (c,t) in zip(correct, total)]))

def print_latex_table_polarity(results):
    """print LateX table as published. Just polarity"""

    correct = [0]*6
    total = [0]*6

    correct[1] = results['by_category']['polarity_particle_kein_ins']['correct']
    total[1] = results['by_category']['polarity_particle_kein_ins']['total']

    correct[4] = results['by_category']['polarity_particle_kein_del']['correct']
    total[4] = results['by_category']['polarity_particle_kein_del']['total']

    correct[0] = results['by_category']['polarity_particle_nicht_ins']['correct']
    total[0] = results['by_category']['polarity_particle_nicht_ins']['total']

    correct[3] = results['by_category']['polarity_particle_nicht_del']['correct']
    total[3] = results['by_category']['polarity_particle_nicht_del']['total']

    correct[2] = results['by_category']['polarity_affix_ins']['correct']
    total[2] = results['by_category']['polarity_affix_ins']['total']

    correct[5] = results['by_category']['polarity_affix_del']['correct']
    total[5] = results['by_category']['polarity_affix_del']['total']

    print(' & '.join(['{0}'.format(t) for t in total]))
    print(' & '.join(['{0:.1f}'.format(c/t*100) for (c,t) in zip(correct, total)]))

def main(reference, scores, maximize, categories, verbose, fd, latex, latex_polarity):

    results = count_errors(reference, scores, maximize, categories, verbose)

    print_statistics(results)
    print()
    print('statistics by error category')
    print_statistics_by_category(results)
    print()
    print('statistics by distance')
    print_statistics_by_distance(results)
    print()
    print('statistics by frequency in training data')
    print_statistics_by_frequency(results)
    print()
    if fd:
        print('statistics by frequency and distance')
        print_statistics_by_frequency_and_distance(results)
        print()
    if latex:
        print('LaTeX table')
        print_latex_table(results)
    if latex_polarity:
        print('LaTeX table (polarity)')
        print_latex_table_polarity(results)



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action="store_true", help="verbose mode (prints out all wrong classifications)")
    parser.add_argument('--maximize', action="store_true", help="Use for model where higher means better (probability; log-likelhood). By default, script assumes lower is better (negative log-likelihood).")
    parser.add_argument('--reference', '-r', type=argparse.FileType('r'),
                        required=True, metavar='PATH',
                        help="Reference JSON file")
    parser.add_argument('--scores', '-s', type=argparse.FileType('r'),
                        default=sys.stdin, metavar='PATH',
                        help="File with scores (one per line)")
    parser.add_argument('--categories', nargs="+", default=ERROR_CATEGORIES, choices=ERROR_CATEGORIES,
                        help="List of error categories to include in statistics (default: all)")
    parser.add_argument('--fd', action="store_true", help="print statistics by frequency and distance.")
    parser.add_argument('--latex', action="store_true", help="print latex table.")
    parser.add_argument('--latex-polarity', action="store_true", help="print latex table (for polarity).")


    args = parser.parse_args()
    main(args.reference, args.scores, args.maximize, args.categories, args.v, args.fd, args.latex, args.latex_polarity)
