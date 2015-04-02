DROP TABLE IF EXISTS wikidata_instanceof CASCADE;
CREATE TABLE wikidata_instanceof (
	item_id int,
        clazz_id int
); -- DISTRIBUTED BY (mention_id);
