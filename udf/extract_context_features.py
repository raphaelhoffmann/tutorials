#! /usr/bin/env python3

import fileinput
import os.path
import sys
import collections

# BASE_DIR denotes the application directory
BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")


def generate_features(sent_id, mention_num, w_from, w_to, words, poses, phrases):
    features = []
    
    # other named entities in same sentence
    for phrase in phrases:
        if not phrase[0] == w_from:
            phrase_str = '_'.join(words[phrase[0]:phrase[1]]).replace("'", "")
            features.append("'NEAR_" + phrase_str + "'")

    # prefix/suffix features
    for i in range(1,4):
        if w_from - i >= 0:
            before = '_'.join(words[w_from-i:w_from]).replace("'", "")
            features.append("'BEFORE_" + before + "'")
        if w_to + i <= len(words):
            after = '_'.join(words[w_to:w_to+i]).replace("'", "")
            features.append("'AFTER_" + after + "'")

    features_str = '{' + ','.join(features) + '}'
    print('\t'.join([sent_id, mention_num, features_str]))


def generate_nnp_phrases(words, poses):
    num_words = len(words)
    i = 0
    while i < num_words:
        j = i
        while j < num_words and poses[j].startswith('NNP'):
            j += 1
        if j > i:
            yield [i, j]
        i = j + 1


if __name__ == "__main__":
    with fileinput.input() as input_files:
        for line in input_files:
            #print(line, file=sys.stderr)
            sent_id, mention_num, w_from_str, w_to_str, words_str, poses_str = line.split('\t')
            words = words_str.split(' ')
            poses = poses_str.split(' ')
            w_from = int(w_from_str)
            w_to = int(w_to_str)
            phrases = generate_nnp_phrases(words, poses)
            generate_features(sent_id, mention_num, w_from, w_to, words, poses, phrases)
