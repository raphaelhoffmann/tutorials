#! /usr/bin/env python3

import fileinput
import os.path
import sys
import collections

# BASE_DIR denotes the application directory
BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")



def bool_to_string(b):
    if b == None:
        return '\\N'
    elif b:
        return '1'
    else:
        return '0'

def arr_to_string(a):
    return "{" + ','.join(a) + "}"

def generate_candidates(doc_id, mention_ids, names, w_froms, w_tos):
    for i, mention_id in enumerate(mention_ids):
       ni = names[i]
       for j in range(0, i+1):
           nj = names[j]
           proto_mention_id = mention_ids[j]

           # check if name is compatible, or simply add all
           
           features = []
           if ni.lower().startswith(nj.lower()):
               features.append('IS_PREFIX')

           #if ni.lower() == nj.lower():
           #    features.append('IS_IGNORECASE_EQUAL')

           is_correct = None 
           print('\t'.join(['\\N', mention_id, proto_mention_id, bool_to_string(is_correct), arr_to_string(features)]))


if __name__ == "__main__":
    with fileinput.input() as input_files:
        for line in input_files:
            #print(line, file=sys.stderr)
            doc_id, mention_ids_str, names_str, w_froms_str, w_tos_str = line.split('\t')
            mention_ids = mention_ids_str.split(' ')
            names = names_str.split('|^|')
            w_froms = [ int(f) for f in w_froms_str.split(' ') ]
            w_tos = [ int(t) for t in w_tos_str.split(' ') ]
            generate_candidates(doc_id, mention_ids, names, w_froms, w_tos)

