DROP TABLE IF EXISTS orglinks CASCADE;
CREATE TABLE orglinks (
	id bigint,
        mention_id varchar(100),
	proto_mention_id varchar(100),
        is_link boolean,
        features text[]
); -- DISTRIBUTED BY (mention_id);
