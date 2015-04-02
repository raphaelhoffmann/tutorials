DROP TABLE IF EXISTS wikidata_names CASCADE;
CREATE TABLE wikidata_names (
	item_id int,
        language varchar(2),
        label varchar(10),
        name varchar(255)
); -- DISTRIBUTED BY (mention_id);
