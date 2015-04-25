DROP TABLE IF EXISTS orgs CASCADE;
CREATE TABLE orgs (
	id bigint,
        mention_id varchar(100),
        document_id varchar(100),
	sentence_num int,
	mention_num int,
	name varchar(100),
        w_from int,
        w_to int,
        is_location boolean,
        ticker varchar(50)
); -- DISTRIBUTED BY (mention_id);
