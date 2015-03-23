DROP TABLE IF EXISTS locations CASCADE;
CREATE TABLE locations (
	id bigint,
	sent_id int,
	mention_num int,
	mention_str varchar(100),
        w_from int,
        w_to int,
	value int
); --DISTRIBUTED BY (mention_id);
