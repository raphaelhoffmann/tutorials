DROP TABLE IF EXISTS entities_lists CASCADE;
CREATE TABLE entities_lists (
        document_id varchar(100),
	sentence_id varchar(100),
	mention_num int,
        list_id varchar(100) 
); -- DISTRIBUTED BY (mention_id);
