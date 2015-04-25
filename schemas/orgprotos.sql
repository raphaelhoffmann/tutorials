DROP TABLE IF EXISTS orgprotos CASCADE;
CREATE TABLE orgprotos (
	id bigint,
        proto_mention_id varchar(100),
	name varchar(100),
        is_proto boolean
); -- DISTRIBUTED BY (mention_id);
