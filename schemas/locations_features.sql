DROP TABLE IF EXISTS locations_features CASCADE;
CREATE TABLE locations_features (
	sent_id int,
	mention_num int,
	loc_id int,
        feature varchar(100)
); --DISTRIBUTED BY (mention_id);
