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
company_suffixes = frozenset(['AB', 'AG', 'GmbH', 'SE', 'Plc', 'Plc.', 'Ltd', 'Ltd.', 'Co.', 'Co', 'Corp', 'Corp.', 'Corporation', 'Inc', 'Inc.', 'Associates', 'Bros.', 'Bank'])

other = frozenset(['Committee', 'Department', 'Government', 'Federation', 'Council', 'Ministry'])


def bool_to_string(b):
    if b == None:
        return '\\N'
    elif b:
        return '1'
    else:
        return '0'

def is_angle_bracketed(word):
    return word.startswith("<") and word.endswith(">") and len(word) >= 3

def generate_candidates(document_id, sentence_num, words, poses, phrases):
    mention_num = 0
    for phrase in phrases:
        t_from = phrase[0]
        t_to = phrase[1]

        # consider three cases wrt presence of <>
        # 1. <Apple Inc>
        # 2. Apple Inc <AAPL>
        # 3. Apple Inc

        name = ''
        ticker = ''
        last = words[phrase[1]-1]

        # 1. <Apple Inc>
        if phrase[1] - phrase[0] == 1 and is_angle_bracketed(last):
            name = last[1:-1]

        # 2. Apple Inc <AAPL>
        elif is_angle_bracketed(last):
            name = ' '.join(words[phrase[0]:phrase[1]-1])
            ticker = last[1:-1]

        # 3. Apple Inc
        else:
            name = ' '.join(words[phrase[0]:phrase[1]])

        is_company = None
        if not ticker == '':
            is_company = True
        for s in company_suffixes:
            if name.endswith(' ' + s):
                is_company = True

        if not is_company:
            if name in months:
                is_company = False
            for w in words:
                if w in titles:
                    is_company = False 
                if w in other:
                    is_company = False

        mention_id = document_id + '_' + str(sentence_num) + '_' + str(phrase[0]) + '_' + str(phrase[1])


        # distant supervision based on knowledge base
        #is_location = '\\N'
        #if mention_str in location_set and not(mention_str in person_set) and not(mention_str in company_set):
        #    is_location = '1'
        #if not(mention_str in location_set) and mention_str in person_set and not(mention_str in company_set):
        #    is_location = '0'
        #if not(mention_str in location_set) and not(mention_str in person_set) and mention_str in company_set:
        #    is_location = '0'
        #if not(mention_str in location_set) and not(mention_str in person_set) and not(mention_str in company_set):
        #    is_location = '\\N'

        # distant supervision based on common sense knowledge
        #first_word = words[t_from]
        #last_word = words[t_to - 1]
        #if last_word in org_types:
        #    is_location = '0'
        #if first_word in months:
        #    is_location = '0'
        #for w in words[t_from:t_to]:
        #    if w in titles:
        #        is_location = '0'       
        #if last_word.endswith('>'):
        #    is_location = '0'

        print('\t'.join(['\\N', mention_id, document_id, str(sentence_num), str(mention_num), name, str(t_from), str(t_to), bool_to_string(is_company), ticker]))
        mention_num += 1

def generate_nnp_phrases(words, poses):
    num_words = len(words)
    i = 0
    spans = []
    while i < num_words:
        j = i
        while j < num_words and poses[j].startswith('NNP'):
            j += 1
        if j > i:
            spans.append([i, j])
        i = j + 1

    # also consider cases where two sequences of NNPs are connected by 'and'
    and_spans = []
    for i in range(0, len(spans) - 1):
        s1 = spans[i]
        s2 = spans[i+1]
        if s1[1] + 1 == s2[0] and words[s1[1]] == 'and':
            # exclude some bad combinations
            ok = True
            for j in range(s1[0], s1[1]):
               if words[j] in months or words[j] in titles or words[j] in other or words[j] in company_suffixes:
                   ok = False
            if ok:
                and_spans.append([s1[0],s2[1]])
    return spans + and_spans

def generate_title_phrases(document_id, words):
    sentence_num = -1
    mention_num = 0
    # we will ignore information in titles for the most part
    # however, we will identify ticker symbols, and company names
    # next to ticker symbols, to help later disambiguation
    for i, w in enumerate(words):
        if w.startswith("<") and w.endswith(">"):
            # it's either a company name or ticker symbol
            tick_or_name = w[1:-1]
            if len(tick_or_name) == 0:
                continue
            # check if the words before it start with the ticker letter
            before = ' '.join(words[0:i])
            if before.startswith(tick_or_name[0]):
                #print(before + '\t' + tick_or_name, file=sys.stderr)
                mention_id = document_id + '_' + str(sentence_num) + '_' + str(0) + '_' + str(i+1)
                mention_str = before
                is_company = 'True'
                ticker = tick_or_name
                print('\t'.join(['\\N', mention_id, document_id, str(sentence_num), str(mention_num), mention_str, str(0), str(i+1), is_company, ticker]))    
                mention_num += 1
                continue
            # check sequence of multiple words for first letters etc., looks like company name
            # todo
            # use words inside <> as company name
            mention_id = document_id + '_' + str(sentence_num) + '_' + str(i) + '_' + str(i+1)
            mention_str = tick_or_name
            is_company = 'True'
            ticker = ''
            print('\t'.join(['\\N', mention_id, document_id, str(sentence_num), str(mention_num), mention_str, str(i), str(i+1), is_company, ticker]))    
            mention_num += 1


if __name__ == "__main__":
    with fileinput.input() as input_files:
        for line in input_files:
            #print(line, file=sys.stderr)
            doc_id, words_str, poses_str, title_words_str = line.split('\t')
            sent_words_str = words_str.split('|^|')
            sent_poses_str = poses_str.split('|^|')
            sent_words = [ s.split(' ') for s in sent_words_str ]
            sent_poses = [ s.split(' ') for s in sent_poses_str ]
            title_words = title_words_str.split(' ')


            title_phrases = generate_title_phrases(doc_id, title_words)

            for i in range(0, len(sent_words)):
                sentence_num = str(i)
                phrases = generate_nnp_phrases(sent_words[i], sent_poses[i])
                generate_candidates(doc_id, sentence_num, sent_words[i], sent_poses[i], phrases)

 
