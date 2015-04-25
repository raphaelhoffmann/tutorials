#! /usr/bin/env python3

import fileinput
import os.path
import sys
import collections

# BASE_DIR denotes the application directory
BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")

location_ids_set = set()
person_ids_set = set()
company_ids_set = set()
with open(BASE_DIR + "/data/wikidata/transitive.tsv", 'rt') as transitive_file:
    print('loading transitive.tsv', file=sys.stderr)
    for line in transitive_file:
        cols = line.split('\t')
        item_id = int(cols[0])
        clazz = int(cols[1])
        if clazz == 2221906:
            location_ids_set.add(item_id)
        if clazz == 783794:
            company_ids_set.add(item_id)
        if clazz == 5:
            person_ids_set.add(item_id)
    print('done', file=sys.stderr)

location_set = set()
person_set = set()
company_set = set()
with open(BASE_DIR + "/data/wikidata/names.tsv", 'rt') as names_file:
    print('loading names.tsv', file=sys.stderr)
    for line in names_file:
        cols = line.split('\t')
        item_id = int(cols[0])
        language = cols[1]
        label = cols[2]
        name = cols[3].rstrip()
        if item_id in location_ids_set:
            location_set.add(name)
        if item_id in person_ids_set:
            person_set.add(name)
        if item_id in company_ids_set:
            company_set.add(name)

# We are looking for the longest sequences of phrases of the form
# [ ], [ ], [ ], and [ ]   (2 or more)
# [ ], [ ], [ ], or [ ]    (2 or more)
# [ ], [ ], [ ]   (at least 3) 

def write_list(list_id, document_id, sentence_id, list_from, list_to):
    for i in range(list_from, list_to):
        full_list_id = str(document_id) + '_' + str(list_id)
        #print('\t'.join([document_id, sentence_id, str(i), str(full_list_id)]), file=sys.stderr)
        print('\t'.join([document_id, sentence_id, str(i), str(full_list_id)]))



def generate_candidates(document_id, sentence_id, words, poses, phrases):
    list_id = 0
    list_from = -1
    last_to = -1
    mention_num = 0
    for phrase in phrases:
        t_from = phrase[0]
        t_to = phrase[1]
        if list_from == -1:
            list_from = mention_num
        else:
            sep = ' '.join(words[last_to:t_from])
            in_list = False
            last = False
            if sep == ',':
               in_list = True
            if sep == ', and' or sep == ', or' or sep == 'and' or sep == 'or':
               in_list = True
               last = True
            if last:
               # write list
               write_list(list_id, document_id, sentence_id, list_from, mention_num+1)
               # reset
               list_id += 1
               list_from = -1
               
            if not in_list:
               # write list
               if mention_num - list_from >= 3:
                   write_list(list_id, document_id, sentence_id, list_from, mention_num)
                   # reset
                   list_id += 1
               list_from = -1
        last_to = t_to
        mention_num += 1
        #mention_id = sent_id + '_' + str(phrase[0]) + '_' + str(phrase[1])


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
            doc_id, sent_id, words_str, poses_str = line.split('\t')
            words = words_str.split(' ')
            poses = poses_str.split(' ')
            phrases = generate_nnp_phrases(words, poses)
            generate_candidates(doc_id, sent_id, words, poses, phrases)

 
