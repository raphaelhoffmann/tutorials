#!/bin/bash

cd $(dirname $0)/..

. ./env_local.sh

dropdb $DBNAME
createdb $DBNAME

psql -c """
  drop table if exists sentences;
  create table sentences(
    sent_id int,
    words text,
    poses text);""" $DBNAME

psql -c """copy sentences from '$(pwd)/data/sentences';""" $DBNAME

