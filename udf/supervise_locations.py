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

def supervise(sent_id, mention_num, mention_str, w_from_str, w_to_str, value):
    matches = cities_dict.get(mention_str)
    
    true_str = '\\N'

    # map all locations that are unique
    if len(matches) == 1:
       true_str = str(matches[0].id)
    else:
       # prefer locations that are both largest and in the US
       largest = matches[0]
       for m in matches:
           if m.population > largest.population:
               largest = m
       if m.country_code == 'US':
           true_str = str(largest.id)

    print('\t'.join(['\\N', sent_id, mention_num, mention_str, w_from_str, w_to_str, true_str]))

    # map all locations with area or zip code
    # TODO

if __name__ == "__main__":
    with fileinput.input() as input_files:
        for line in input_files:
            sent_id, mention_num, mention_str, w_from_str, w_to_str, value = line.split('\t')
            supervise(sent_id, mention_num, mention_str, w_from_str, w_to_str, value)           

