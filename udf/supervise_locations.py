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

Loc = collections.namedtuple('Loc', ['id', 'name', 'lat', 'lon', 'country_code', 'population'])

cities_dict = dict() 
with open(BASE_DIR + "/download/cities1000.txt", 'rt') as cities_file:
    for line in cities_file:
        cols = line.split('\t')
        id = int(cols[0])
        name = cols[1]
        lat = float(cols[4])
        lon = float(cols[5])
        country_code = cols[8]
        population = int(cols[14])
        loc = Loc(id=id,name=name,lat=lat,lon=lon,country_code=country_code,population=population)
        li = cities_dict.setdefault(name, [])
        li.append(loc)

def supervise(sent_id, mention_num, mention_str, w_from_str, w_to_str, value):
    matches = cities_dict.get(mention_str)

    # map all locations that are unique
    if len(matches) == 1:
       print('\t'.join([sent_id, mention_num, mention_str, w_from_str, w_to_str, '1']))

    # map all locations with area or zip code
    # TODO

if __name__ == "__main__":
    with fileinput.input() as input_files:
        for line in input_files:
            sent_id, mention_num, mention_str, w_from_str, w_to_str, value = line.split('\t')
            

