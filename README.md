LingEval97
==========

A test set of contrastive translation pairs for machine translation analysis
----------------------------------------------------------------------------

This directory contains a set of 97000 contrastive translation pairs for the
analysis of (neural) machine translation. It is based on the EN-DE test sets
from the WMT shared translation task 2009-2016.

How does the evaluation work?
-----------------------------

The core idea is that we measure whether a reference translation is more probable under a NMT model
than a contrastive translation which introduces a specific type of error. Starting from the WMT test sets,
we automatically introduced errors into the reference translations. After an NMT model scores both the original
translations and all contrastive translations in the test set, we compute the accuracy of the model for each error category,
that is the relative number of times that the model gives a higher probability to the human reference than the contrastive translation.

Usage instructions
------------------

 - extract plain text parallel corpus:
   python json_to_plaintext.py lingeval97

 - preprocess lingeval97.{de,en} and score each sentence pair with an English-German NMT model.
   In the directory `baselines`, we provide the raw output of all baselines reported in the paper (see below for reference).

 - evaluate a system:
   python evaluate.py -r lingeval97.json < baselines/sennrich2016.scores

What error types are included in the test set?
----------------------------------------------

We automatically introduce a number of translation errors that are known to be challenging for MT:

 - noun phrase agreement: German determiners must agree with their head noun in case, number, and gender. We randomly change the gender of a singular definite determiner to introduce an agreement error.
 - subject-verb agreement: subjects and verbs must agree with one another in grammatical number and person. We swap the grammatical number of a verb to introduce an agreement error with the subject.
 - subject adequacy: if the German subject is `sie` ('they', 'she'), changing the grammatical number of the verb does not make the translation ungrammatical, but changes the meaning.
 - auxiliaries: some German verbs are accompanied by the auxiliary `haben` ('have') others by `sein` ('be'). We introduce errors by swapping the auxiliary.
 - separable verb particle: in German, verbs and their separable prefix often form a discontiguous semantic unit. We replace a separable verb particle with one that has never been observed with the verb in the training data.
 - polarity: arguably, polarity errors are undermeasured the most by string-based MT metrics, since a single word/morpheme can reverse the meaning of a translation. We reverse polarity in one of six ways:
   - deleting the negation particle `nicht` ('not')
   - replacing the negative determiner `kein` ('no') with its positive counterpart `ein` ('a')
   - deleting the negation prefix `un-`
   - inserting the negation particle `nicht` ('not'). We use POS patterns of the monolingual training corpus to find plausible insertion spots.
   - replacing the determiner `ein` ('a') with its negative counterpart `kein` ('no')
   - inserting the negation prefix '-un-'.
 - compounds: for German compounds that consist of at least 3 segments, and were unseen in the training data, we swap the first two segments.
 - transliteration: subword-level models should be able to copy or transliterate names, even unseen ones. For names that were unseen in the training data, we swap two adjacent characters.

Data format
-----------

For scoring, the test set can be extracted to raw text with `json_to_plaintext.py`.
The dataset `lingeval97.json` also contains annotations for more in-depth analysis.
Each entry in the dataset has the following keys:

 - source: the source sentence
 - reference: the human reference translation from the original test set
 - origin: the test set ID and sentence index
 - errors: a list of contrastive translations. Each has the following keys:
   - type: a string identifying the type of error inserted
   - contrastive: the contrastive translation
   - distance: for errors involving multiple words (agreement, verb particles, auxiliaries), the distance in words between the two.
   - frequency: for errors pertaining to content words, their training set frequency. For subject-verb-agreement, the smaller frequency is reported.

an example is shown here:

```
  {
    "source": "Prague Stock Market falls to minus by the end of the trading day",
    "reference": "Die Prager Börse stürzt gegen Geschäftsschluss ins Minus.",
    "origin": "newstest2009.1",
    "errors": [
      {
        "type": "np_agreement",
        "contrastive": "Der Prager Börse stürzt gegen Geschäftsschluss ins Minus.",
        "distance": 2,
        "frequency": 2020
      },
      {
        "type": "polarity_particle_nicht_ins",
        "contrastive": "Die Prager Börse stürzt gegen Geschäftsschluss nicht ins Minus."
      },
      {
        "type": "subj_verb_agreement",
        "contrastive": "Die Prager Börse stürzen gegen Geschäftsschluss ins Minus.",
        "distance": 1,
        "frequency": 286
      }
    ]
  }
```



Baseline results
----------------

Some results are reported in the referenced paper. Here are the full results obtained with `evaluate.py -r lingeval97.json < baselines/sennrich2016.scores':

```
total : 94732 97408 0.972527923784

statistics by error category
np_agreement : 21540 21813 0.987484527575
subj_verb_agreement : 33907 35105 0.96587380715
subj_adequacy : 2266 2520 0.899206349206
polarity_particle_nicht_del : 2733 2919 0.93627954779
polarity_particle_kein_del : 495 538 0.920074349442
polarity_affix_del : 518 586 0.883959044369
polarity_particle_nicht_ins : 1259 1297 0.970701619121
polarity_particle_kein_ins : 10192 10219 0.997357862805
polarity_affix_ins : 11018 11244 0.97990039132
auxiliary : 4837 4950 0.977171717172
verb_particle : 2355 2450 0.961224489796
compound : 249 277 0.898916967509
transliteration : 3363 3490 0.963610315186

statistics by distance
distance 1: 35960 36685 0.98023715415
distance 2: 9611 9861 0.974647601663
distance 3: 4626 4807 0.962346577907
distance 4: 3094 3263 0.948207171315
distance 5: 2480 2598 0.954580446497
distance 6: 2004 2105 0.952019002375
distance 7: 1614 1693 0.953337271116
distance 8: 1253 1317 0.951404707669
distance 9: 963 1016 0.947834645669
distance 10: 721 757 0.952443857332
distance 11: 588 617 0.952998379254
distance 12: 439 461 0.952277657267
distance 13: 334 355 0.940845070423
distance 14: 233 242 0.962809917355
distance 15: 202 217 0.930875576037
distance >15: 783 844 0.927725118483

statistics by frequency in training data
>10k : 21533 21901 0.983197114287
>5k : 7506 7639 0.982589344155
>2k : 10475 10673 0.981448514944
>1k : 6617 6809 0.971802026729
>500 : 5857 6044 0.969060225017
>200 : 6170 6366 0.969211435752
>100 : 3724 3875 0.961032258065
>50 : 2810 2943 0.954808019028
>20 : 2875 3022 0.951356717406
>10 : 1525 1621 0.940777297964
>5 : 1171 1248 0.938301282051
>2 : 1060 1127 0.940550133097
2 : 552 587 0.940374787053
1 : 846 892 0.948430493274
0 : 7332 7688 0.953694068678
```

more detailed statistics are possible, for instance reporting distance-level statistics for specific categories (use `--categories`).

The command-line option `--latex` collates and formats statistics like in the paper referenced below.

Use the command-line option `-v` to print out all contrastive pairs (of the active categories) for which the model prefers the contrastive translation.

References
----------

The test set is described in:

Sennrich, Rico (2016): How Grammatical is Character-level Neural Machine Translation? Assessing MT Quality with Contrastive Translation Pairs.
