#! /bin/bash

cd $(dirname $0)/..

. ./env_local.sh

sql=$(cat <<EOF
drop table if exists cities1000;
create table cities1000 (
  geonameid int,
  name varchar(200),
  asciiname varchar(200),
  alternatenames varchar(10000),
  latitude real,
  longitude real,
  feature_class char(1),
  feature_code varchar(10),
  country_code char(2),
  cc2 varchar(60),
  admin1_code varchar(20),
  admin2_code varchar(80),
  admin3_code varchar(20),
  admin4_code varchar(20),
  population bigint,
  elevation int,
  dem int,
  timezone varchar(40),
  modification_date date
);
copy cities1000 from '$(pwd)/data/cities1000.txt' with null as '';
EOF
)

echo $sql | psql $DBNAME

