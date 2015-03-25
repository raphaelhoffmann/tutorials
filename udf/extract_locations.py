#! /usr/bin/env python3

import fileinput
import os.path
import sys

# BASE_DIR denotes the application directory
BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")

cities_set = set() 
with open(BASE_DIR + "/data/cities1000_with_ids.txt", 'rt') as cities_file:
    for line in cities_file:
        cols = line.split('\t')
        name = cols[2]
        cities_set.add(name)


def generate_candidates(sent_id, words, poses, phrases):
    mention_num = 0
    for phrase in phrases:
        mention_str = ' '.join(words[phrase[0]:phrase[1]])
        if not mention_str in cities_set:
            return
        mention_id = sent_id + '_' + str(phrase[0]) + '_' + str(phrase[1])
        print('\t'.join(['\\N', mention_id, str(sent_id), str(mention_num), mention_str, str(phrase[0]), str(phrase[1]), '\\N']))
        mention_num += 1

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
            sent_id, words_str, poses_str = line.split('\t')
            words = words_str.split(' ')
            poses = poses_str.split(' ')
            phrases = generate_nnp_phrases(words, poses)
            generate_candidates(sent_id, words, poses, phrases)
