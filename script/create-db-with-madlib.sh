#!/bin/bash

cd $(dirname $0)/..

. ./env_local.sh

dropdb $DBNAME
createdb $DBNAME

/usr/local/madlib/bin/madpack -p $DBMS -c $PGUSER@$PGHOST/$DBNAME install


