DROP TABLE IF EXISTS entities_features CASCADE;
CREATE TABLE entities_features (
        sentence_id varchar(100),
        mention_num int,
        features text[]
); -- DISTRIBUTED BY (mention_id);
