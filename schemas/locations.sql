DROP TABLE IF EXISTS locations CASCADE;
CREATE TABLE locations (
	id bigint,
        mention_id varchar(100),
	sentence_id varchar(100),
	mention_num int,
	mention_str varchar(100),
        w_from int,
        w_to int,
	loc_id int,
        is_correct boolean,
        features text[]
); -- DISTRIBUTED BY (mention_id);
