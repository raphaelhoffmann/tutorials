DROP TABLE IF EXISTS locations_features CASCADE;
CREATE TABLE locations_features (
        mention_id varchar(100),
	loc_id int,
        feature varchar(100)
) DISTRIBUTED BY (mention_id);
