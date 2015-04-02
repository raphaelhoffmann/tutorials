#!/bin/sh
    
psql -h localhost -p 5432 geo -f `pwd`/../schemas/wikidata_names.sql
psql -h localhost -p 5432 geo -f `pwd`/../schemas/wikidata_coordinate_locations.sql
psql -h localhost -p 5432 geo -f `pwd`/../schemas/wikidata_instanceof.sql

psql -h localhost -p 5432 geo -c "copy wikidata_names from '`pwd`/../../../wikidata/names.tsv' CSV DELIMITER E'\t' QUOTE E'\1';"
psql -h localhost -p 5432 geo -c "copy wikidata_coordinate_locations from '`pwd`/../../../wikidata/coordinate_location.tsv';"
psql -h localhost -p 5432 geo -c "copy wikidata_instanceof from '`pwd`/../../../wikidata/items_details.tsv';"


