DROP TABLE IF EXISTS sentences_titles;
CREATE TABLE sentences_titles(
  document_id  bigint,    -- which document it comes from
  sentence     text,      -- sentence content
  words        text[],    -- array of words in this sentence
  lemma        text[],    -- array of lemmatized words
  pos_tags     text[],    -- array of part-of-speech tags
  dependencies text[],    -- array of dependency paths
  ner_tags     text[],    -- array of named entity tags (PERSON, LOCATION, etc)
  sentence_offset bigint, -- which sentence (0, 1, 2...) is it in document
  sentence_id  text       -- unique identifier for sentences
  );
