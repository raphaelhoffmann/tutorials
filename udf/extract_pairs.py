#! /usr/bin/env python3

import fileinput
import os.path
import sys
import collections

# BASE_DIR denotes the application directory
BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")

Loc = collections.namedtuple('Loc', ['geo_id', 'name'])

cities_dict = dict()
with open(BASE_DIR + "/../../wikidata/names.tsv", 'rt') as cities_file:
    for line in cities_file:
        cols = line.split('\t')
        item_id = int(cols[0])
        language = cols[1]
        label = cols[2]
        name = cols[3]
        loc = Loc(geo_id=geo_id,name=name)
        li = cities_dict.setdefault(name, [])
        li.append(loc)

#Can = collections.namedtuple('Can', ['id', 'mention_id', 'sent_id', 'mention_num', 'mention_str', 'w_from', 'w_to', 'loc_id', 'is_correct', 'features'])

def generate_candidates(sent_id, words, poses, phrases):
    mention_num = 0
    for phrase in phrases:
        t_from = phrase[0]
        t_to = phrase[1]
        mention_str = ' '.join(words[phrase[0]:phrase[1]])
        matches = cities_dict.get(mention_str)
        if not matches:
            continue
        
        for loc in matches:

            # generate features
            features = []

            # 1. is_most_populous
            #is_most_populous = True
            #for other in matches:
            #    if other != loc and other.population > loc.population:
            #        is_most_populous = False
            #if is_most_populous:
            #    features.append("is_most_populous")

            # 2. country
            #features.append('country_' + loc.country_code)

            # 3. near_mention_in_sentence
            #for near in phrases:
            #    if near[0] != t_from:
            #        features.append('near_' + '_'.join(words[near[0]:near[1]]))

            features_str = '{' + ','.join(features) + '}'
            mention_id = sent_id + '_' + str(phrase[0]) + '_' + str(phrase[1]) + '_' + str(loc.geonameid)

            # supervise
            true_str = '\\N'

            # map all locations that are unique
            if len(matches) == 1:
                true_str = '1' 
            #else:
            #    # prefer locations that are both largest and in the US
            #    largest = matches[0]
            #    for m in matches:
            #        if m.population > largest.population:
            #            largest = m
            #    if m.country_code == 'US' and m == loc:
            #        true_str = '1'

            print('\t'.join(['\\N', mention_id, str(sent_id), str(mention_num), mention_str, str(phrase[0]), str(phrase[1]), str(loc.geo_id), '\\N', features_str ]))
            print('\t'.join(['\\N', mention_id, str(sent_id), str(mention_num), mention_str, str(phrase[0]), str(phrase[1]), str(loc.geo_id), true_str, features_str ]))

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
