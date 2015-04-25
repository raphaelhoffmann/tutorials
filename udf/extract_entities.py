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

first_names = frozenset([])
last_names = frozenset([])
titles = frozenset(['Chairman', 'Secretary', 'Attorney', 'President', 'Representative', 'Spokesman', 'Delegation', 'Minister', 'Ambassador'])
months = frozenset(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
org_types = frozenset(['Plc', 'Plc.', 'Ltd', 'Ltd.', 'Corp', 'Corp.', 'Corporation', 'Inc', 'Inc.', 'Associates', 'Committee', 'Department', 'Government', 'Federation', 'Council', 'Ministry'])


def generate_candidates(document_id, sentence_id, words, poses, phrases):
    mention_num = 0
    for phrase in phrases:
        t_from = phrase[0]
        t_to = phrase[1]
        mention_str = ' '.join(words[phrase[0]:phrase[1]])
        mention_id = sent_id + '_' + str(phrase[0]) + '_' + str(phrase[1])

        # distant supervision based on knowledge base
        is_location = '\\N'
        if mention_str in location_set and not(mention_str in person_set) and not(mention_str in company_set):
            is_location = '1'
        if not(mention_str in location_set) and mention_str in person_set and not(mention_str in company_set):
            is_location = '0'
        if not(mention_str in location_set) and not(mention_str in person_set) and mention_str in company_set:
            is_location = '0'
        if not(mention_str in location_set) and not(mention_str in person_set) and not(mention_str in company_set):
            is_location = '\\N'

        # distant supervision based on common sense knowledge
        first_word = words[t_from]
        last_word = words[t_to - 1]
        if last_word in org_types:
            is_location = '0'
        if first_word in months:
            is_location = '0'
        for w in words[t_from:t_to]:
            if w in titles:
                is_location = '0'       
        if last_word.endswith('>'):
            is_location = '0'



        print('\t'.join(['\\N', mention_id, document_id, sentence_id, str(mention_num), mention_str, str(t_from), str(t_to), is_location]))
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
            doc_id, sent_id, words_str, poses_str = line.split('\t')
            words = words_str.split(' ')
            poses = poses_str.split(' ')
            phrases = generate_nnp_phrases(words, poses)
            generate_candidates(doc_id, sent_id, words, poses, phrases)

 
