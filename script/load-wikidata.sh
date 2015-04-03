#!/bin/bash

cd $(dirname $0)/..

. ./env_local.sh

psql -h $PGHOST -p $PGPORT $DBNAME -f `pwd`/schemas/wikidata_names.sql
psql -h $PGHOST -p $PGPORT $DBNAME -f `pwd`/schemas/wikidata_coordinate_locations.sql
psql -h $PGHOST -p $PGPORT $DBNAME -f `pwd`/schemas/wikidata_instanceof.sql

psql -h $PGHOST -p $PGPORT $DBNAME -c "copy wikidata_names from '`pwd`/data/wikidata/names.tsv' CSV DELIMITER E'\t' QUOTE E'\1';"
psql -h $PGHOST -p $PGPORT $DBNAME -c "copy wikidata_coordinate_locations from '`pwd`/data/wikidata/coordinate-locations.tsv';"
psql -h $PGHOST -p $PGPORT $DBNAME -c "copy wikidata_instanceof from '`pwd`/data/wikidata/transitive.tsv';"


