#! /usr/bin/env python3

import json 
import collections

BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")
DATA_DIR = BASE_DIR + '/data'

languages = [ 'en' ]

def parse_json(line):
    obj = json.loads(line)
    id = obj['id'][1:]
    #typ = obj['type']
  
    for lang in languages:
        if 'labels' in obj and lang in obj['labels']:
            label = obj['labels'][lang]['value']
            print(id + '\t' + lang + '\t' + 'label' + '\t' + label.replace('\t', ' ').replace('\n', ' '))

        if 'aliases' in obj and lang in obj['aliases']:
            aliases = [a['value'] for a in obj['aliases'][lang]]
            for alias in aliases:
                print(id + '\t' + lang + '\t' + 'alias' + '\t' + alias.replace('\t', ' ').replace('\n', ' '))


with open(DATA_DIR + '/wikidata/dump.json', 'r') as f:
    for line in f:
        line = line.rstrip()
        if line == '[' or line == ']':
            continue
        # strip trailing commas
        line = line.rstrip(',')
        parse_json(line)
