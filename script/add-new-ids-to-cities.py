#! /usr/bin/env python3



out = open('../data/cities1000_with_ids.txt', 'w', encoding='utf-8')

with open('../data/cities1000.txt') as f:
  id = 0
  for line in f:
    print(str(id) + '\t' + line.rstrip(), file=out)
    id += 1

out.close
