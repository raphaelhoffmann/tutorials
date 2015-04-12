#!/bin/bash

cd $(dirname $0)/..

. ./env_local.sh

dropdb $DBNAME
createdb $DBNAME

psql -h $PGHOST -p $PGPORT $DBNAME -f $APP_HOME/schemas/articles.sql

psql -h $PGHOST -p $PGPORT $DBNAME -c """copy articles from '$(pwd)/data/reuters/converted.csv' csv;"""


