#! /usr/bin/env python3

import fileinput
import re
import os.path
import sys
import collections
#import collections.namedtuple

# BASE_DIR denotes the application directory
BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")

Loc = collections.namedtuple('Loc', ['id', 'origid', 'name', 'lat', 'lon', 'country_code', 'population'])

cities_dict = dict() 
with open(BASE_DIR + "/data/cities1000_with_ids.txt", 'rt') as cities_file:
    for line in cities_file:
        cols = line.split('\t')
        id = int(cols[0])
        origid = int(cols[1])
        name = cols[2]
        lat = float(cols[5])
        lon = float(cols[6])
        country_code = cols[9]
        population = int(cols[15])
        loc = Loc(id=id,origid=origid,name=name,lat=lat,lon=lon,country_code=country_code,population=population)
        li = cities_dict.setdefault(name, [])
        li.append(loc)

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

def generate_features(sent_id, words, poses, mention_num, t_from, t_to):
    mention_str = ' '.join(words[t_from:t_to])
    matches = cities_dict.get(mention_str)
    if not matches:
        return
    
    # determine nearby nnps for features
    phrases = generate_nnp_phrases(words, poses)

    #print("found a match for: " + mention_str + " [ " + str(len(matches)) + " ] " , file=sys.stderr)
    for loc in matches:

        # generate features
        features = []

        # 1. is_most_populous
        is_most_populous = True 
        for other in matches:
            if other != loc and other.population > loc.population:
                is_most_populous = False 
        if is_most_populous:
            features.append("is_most_populous")
        
        # 2. country
        features.append('country_' + loc.country_code)

        # 3. near_mention_in_sentence
        for near in phrases:
            if near[0] != t_from:
                features.append('near_' + '_'.join(words[near[0]:near[1]]))
    
        # 4. TODO: CRF FEATURE is_closest_to_previous_location
        for feature in features:
            print('\t'.join([str(sent_id), str(mention_num), str(loc.id), feature]))


if __name__ == "__main__":
    with fileinput.input() as input_files:
        for line in input_files:
            sent_id, words_str, poses_str, mention_num, t_from, t_to = line.split('\t')
            words = words_str.split(' ')
            poses = poses_str.split(' ')
            phrases = generate_nnp_phrases(words, poses)
            generate_features(sent_id, words, poses, mention_num, int(t_from), int(t_to))
