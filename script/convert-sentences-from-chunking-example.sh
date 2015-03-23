#! /usr/bin/env python

def output(id, tokens, poses):
  print(str(id) + '\t' + (' '.join(tokens)) + '\t' + ' '.join(poses))

with open('../data/train_null_terminated.txt') as f:
  tokens = []
  poses = []
  id = 0
  for line in f:
    c1, c2, c3 = line.split(' ')
    if c1 == 'null' and c2 == 'null':
       # new sentence
       output(id, tokens, poses)
       id += 1
       tokens = []
       poses = []
       continue
    tokens.append(c1)
    poses.append(c2)
  output(id, tokens, poses)

