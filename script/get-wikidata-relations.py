#! /usr/bin/env python3

import os
import json 
import collections
import sys

BASE_DIR, throwaway = os.path.split(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(BASE_DIR + "/..")
DATA_DIR = BASE_DIR + '/data'

# Wikidata relations: instance_of (P31)
#                     subclass_of (P279)

# Example 1:
#"claims":{"P31":[{"id":"q136115$3B641BE1-2264-48CC-AB99-BDA76E91B33D","mainsnak":{"snaktype":"value","property":"P31","datatype":"wikibase-item","datavalue":{"value":{"entity-type":"item","numeric-id":4830453},"type":"wikibase-entityid"}},"type":"statement","rank":"normal"}],"P131":[{"id":"q136115$8FB0EF13-A1C9-4989-A0C2-015DE81B7CF1","mainsnak":{"snaktype":"value","property":"P131","datatype":"wikibase-item","datavalue":{"value":{"entity-type":"item","numeric-id":4190},"type":"wikibase-entityid"}},"type":"statement","rank":"normal"}]

# Example 2:
# "P279":[{"id":"Q1301$98439DE1-3FC6-46DD-B5A0-D7FD511D3851","mainsnak":{"snaktype":"value","property":"P279","datatype":"wikibase-item","datavalue":{"value":{"entity-type":"item","numeric-id":244979},"type":"wikibase-entityid"}},"type":"statement","rank":"normal"},{"id":"Q1301$cc02929e-462b-e141-659d-3ca0d10c1899","mainsnak":{"snaktype":"value","property":"P279","datatype":"wikibase-item","datavalue":{"value":{"entity-type":"item","numeric-id":189294},"type":"wikibase-entityid"}},"type":"statement","rank":"normal"}],"P31":[{"id":"Q1301$4AB9DA52-4731-49D1-A6A2-3981B33B6A47","mainsnak":{"snaktype":"value","property":"P31","datatype":"wikibase-item","datavalue":{"value":{"entity-type":"item","numeric-id":11344},"type":"wikibase-entityid"}},"type":"statement","rank":"normal"}],

relations = ['P31', 'P279']

def parse_json(line, w):
  obj = json.loads(line)
  id = obj['id'][1:] # strip Q
  #typ = obj['type']

  if 'claims' in obj:
    claims = obj['claims']
    for r in relations:
      if r in claims:
        rs = claims[r]
        for i in rs:
          try: 
            oid = i['mainsnak']['datavalue']['value']['numeric-id']
            print(str(id) + '\t' + r[1:] + '\t' + str(oid), file=w)
          except KeyError:
            print('ignoring keyerror', file=sys.stderr) 

with open(DATA_DIR + '/wikidata/dump.json', 'r') as f, open(DATA_DIR + '/wikidata/relations.tsv', 'w') as w:
    for line in f:
        line = line.rstrip()
        if line == '[' or line == ']':
            continue
        # strip trailing commas
        line = line.rstrip(',')
        parse_json(line, w)
