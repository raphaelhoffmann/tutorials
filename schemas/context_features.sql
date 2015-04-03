DROP TABLE IF EXISTS context_features CASCADE;
CREATE TABLE context_features (
        sentence_id varchar(100),
        mention_num int,
        features text[]
); -- DISTRIBUTED BY (mention_id);
