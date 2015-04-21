#!/usr/bin/env python

import argparse
import cPickle
import traceback
import logging
import time
import sys

import os
import numpy
import codecs
import search
import utils

from session_encdec import SessionEncoderDecoder 
from numpy_compat import argpartition
from state import prototype_state

logger = logging.getLogger(__name__)

class Timer(object):
    def __init__(self):
        self.total = 0

    def start(self):
        self.start_time = time.time()

    def finish(self):
        self.total += time.time() - self.start_time

def parse_args():
    parser = argparse.ArgumentParser("Sample (with beam-search) from the session model")

    parser.add_argument("--n-samples",
            default="1", type=int,
            help="Number of samples")

    parser.add_argument("--ignore-unk",
            default=True, action="store_false",
            help="Ignore unknown words")

    parser.add_argument("model_prefix",
            help="Path to the model prefix (without _model.npz or _state.pkl)")

    parser.add_argument("context",
            help="File of input contexts (pair of sentences, tab separated)")

    parser.add_argument("--normalize",
            action="store_true", default=False,
            help="Normalize log-prob with the word count")

    parser.add_argument("--verbose",
            action="store_true", default=False,
            help="Be verbose")

    parser.add_argument("changes", nargs="?", default="", help="Changes to state")
    return parser.parse_args()

def main():
    args = parse_args()
    state = prototype_state()

    state_path = args.model_prefix + "_state.pkl"
    model_path = args.model_prefix + "_model.npz"

    with open(state_path) as src:
        state.update(cPickle.load(src))

    logging.basicConfig(level=getattr(logging, state['level']), format="%(asctime)s: %(name)s: %(levelname)s: %(message)s")

    model = SessionEncoderDecoder(state) 
    sampler = search.Sampler(model)

    if os.path.isfile(model_path):
        logger.debug("Loading previous model")
        model.load(model_path)
    else:
        raise Exception("Must specify a valid model path")

    contexts = [[]]
    lines = open(args.context, "r").readlines()
    contexts = [x.strip().split('\t') for x in lines]

    context_samples, \
    context_costs, \
    context_ranks = sampler.sample(contexts,
                         n_samples=args.n_samples,
                         ignore_unk=args.ignore_unk,
                         verbose=args.verbose)
    
    print context_samples, context_costs, context_ranks

    # Write to output file
    output_handle = open(args.context + ".sugg.txt", "w")
    for context_sample in context_samples:
        print >> output_handle, '\t'.join(context_sample)
    output_handle.close()
    output_handle = open(args.context + ".sugg.rnk", "w")
    for context_rank in context_ranks:
        print >> output_handle, '\t'.join(map(str, context_rank))
    output_handle.close()

if __name__ == "__main__":
    main()
