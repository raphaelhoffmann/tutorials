DROP TABLE IF EXISTS wikidata_coordinate_locations CASCADE;
CREATE TABLE wikidata_coordinate_locations (
	item_id int,
        latitude float,
	longitude float
); -- DISTRIBUTED BY (mention_id);
