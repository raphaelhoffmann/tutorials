#! /usr/bin/env python3

import os
import json 
import collections

# compute transitive closure of subclasses of geographic location (2221906)

clazzes = [ 
    2221906, # geographic location
    6256,    # country
    1637706, # city with millions of inhabitants
    1549591, # city with hundreds of thousands of inhabitants
    515,     # city
    783794,  # company
    5        # human
]

BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")
DATA_DIR = BASE_DIR + '/data'

map = {}

def build_map():
    with open(DATA_DIR + '/wikidata/relations.tsv', 'r') as f:
        for line in f:
            id1str,rel,id2str = line.split('\t')
            id1 = int(id1str)
            id2 = int(id2str)
            if not rel == '279':
                continue
            if id2 in map:
                l = map[id2]
            else:
                l = []
                map[id2] = l
            l.append(id1)

def transitive_closure(id, sel):
    if id in sel:
        return
    sel.add(id)
    if id in map:
        subsets = map[id]
        for sid in subsets:
            transitive_closure(sid, sel) 

def get_items(sel, clazz, w):
    with open(DATA_DIR + '/wikidata/relations.tsv', 'r') as f:
        last = -1
        for line in f:
            id1str,rel,id2str = line.split('\t')
            id1 = int(id1str)
            id2 = int(id2str)
            # skip if we have already written this item
            if id1 == last:
                continue
            # skip if relation is not 'instance of'
            if not rel == '31':
                continue
            if id2 in sel:
                print(str(id1) + '\t' + str(clazz), file=w)
                last = id1

with open(DATA_DIR + '/wikidata/transitive.tsv', 'w') as w:
    build_map()
    # compute transitive closure for each class
    for clazz in clazzes:
        sel = set()
        transitive_closure(clazz, sel)
        get_items(sel, clazz, w)

    
