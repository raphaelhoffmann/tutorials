DROP TABLE IF EXISTS entities CASCADE;
CREATE TABLE entities (
	id bigint,
        mention_id varchar(100),
        document_id varchar(100),
	sentence_id varchar(100),
	mention_num int,
	mention_str varchar(100),
        w_from int,
        w_to int,
        is_location boolean
); -- DISTRIBUTED BY (mention_id);
