# Tutorial: Coreference Resolution Within Documents

 
<!--
References to locations are ubiquitous in text, but many such references are ambiguous. For
example, Wikipedia lists [more than 30 locations](https://en.wikipedia.org/wiki/San_Francisco_(disambiguation)) named 'San Francisco', 10 songs with
that name, 2 movies, a magazine, and several other things as well.
In this tutorial, we develop a system that detects mentions of geographic locations
and links these unambiguously to a database of locations.

We start with a corpus of 20,000 news articles, the [Reuters-21578 dataset](http://archive.ics.uci.edu/ml/machine-learning-databases/reuters21578-mld/reuters21578.html), which 
represents articles that appeared on the Reuters newswire in 1987. Our goal is to identify
mentions of locations in these articles and unambiguously link them to entities in [Wikidata](http://www.wikidata.org), 
a community-edited database containing 14 million entities, including more than 2 million 
geographic locations. 

Using wikidata as a database has three major advantages: 

* Wikidata contains not just locations but also many other types of entities in the real 
  world. This makes it easy to re-use the tools developed for this tutorial to other 
  entity linking tasks.
* Wikidata is dense in the sense that it contains many attributes and relationships
  between entities. As we will see, we can exploit this information to more accurately
  disambiguate mentions of entities. 
* Wikidata has an active community enhancing the data, absorbing other available sources
  (including Freebase) and adding open-data links to other resources. Wikidata is thus
  growing quickly.

This tutorial assumes that you are already familiar with setting up and running
deepdive applications. 
-->

## Preparing the Reuters dataset

If you haven't done so already, download the Reuters corpus from [UC Irvine repository](http://archive.ics.uci.edu/ml/machine-learning-databases/reuters21578-mld/reuters21578.html).
The original data is in SGML which we convert to JSON for readability and CSV for loading into the database. The following scripts perform these steps:

    script/fetch-reuters.py
    script/get-reuters-json-csv.py

Next, we create a schema for articles in the database and load the data. Both can be done by running:

    script/load-reuters.py

To be able to iterate on our system more quickly, we first take only a sample of articles. At the end, we
can then process the entire corpus. To create a sample, run:

    psql geo
    CREATE TABLE articles_sample AS SELECT * FROM articles ORDER BY random() LIMIT 1000;

The articles are stored as strings of text. To more easily identify mentions we would like
to compute word boundaries by running a tokenizer, splitting sentences, and computing part-of-speech tags. Deepdive offers the 
`nlp_extractor` for that. We can run the `nlp_extractor` on the command line or as an extraction 
step in our deepdive application. We do the latter and add extractors for processing article bodies and article titles to `app2.conf`:

```
extract_preprocess_bodies: {
  style: json_extractor
  before: psql -h ${PGHOST} -p ${PGPORT} -d ${DBNAME} -f ${APP_HOME}/schemas/sentences.sql
  input: """
         SELECT id, body
         FROM articles_sample
         WHERE NOT BODY IS NULL
         ORDER BY id ASC
         """
  output_relation: sentences
  udf: ${DEEPDIVE_HOME}/examples/nlp_extractor/run.sh -k id -v body -l 100 -t 16 -a "tokenize,ssplit,pos"
}

extract_preprocess_titles: {
  style: json_extractor
  before: psql -h ${PGHOST} -p ${PGPORT} -d ${DBNAME} -f ${APP_HOME}/schemas/sentences_titles.sql
  input: """
         SELECT id, title
         FROM articles_sample
         WHERE NOT TITLE IS NULL
         ORDER BY id ASC
         """
  output_relation: sentences_titles
  udf: ${DEEPDIVE_HOME}/examples/nlp_extractor/run.sh -k id -v title -l 100 -t 16 -a "tokenize,ssplit,pos"
}
```

Note: We set `nlp_extractor` to only run its tokenize, ssplit, and pos annotators. We do not run the
parse annotator (which would normally be included), since we don't need parses and parsing requires
many hours of computation time on this corpus.


## Generating Candidates

* extract named entities from titles and bodies
* create cluster prototypes (the representative mentions for each coreference cluster)
* create potential links
* use statistical inference


To find references to named entities, we first identify spans in the article text 
that may represent such references. We compute all sequences of consecutive tokens 
with NNP part-of-speech tags. For example, for the sentence:

    NNP  VB               NNP NNP       .
    Cook gave a speech in San Francisco . 

we would identify the two spans `Cook` and `San Francisco`. Sometimes, named entities
also contain the word 'and', for example `Cable and Wireless Corp`. We also consider
such spans.

A naive approach to our entity linking problem would simply return all clusters of
named entities that are exactly matching strings. There are several problems to this:
  
1. After an entity is introduced, it is often referred to by a pronoun. For example,
   `Cable and Wireless Corp` and `it`.

2. After an entity is introduced, it is often referred to by a nominal. For example,
   `Cable and Wireless Corp` and `the company`.

3. After an entity is introduced, it is often referred to by a shorter form. For example,
   `Cable and Wireless Corp` and `Cable and Wireless`.

4. The text may explicity introduce synonyms, and later use those. For example,
   `Cable and Wireless Corp (CAW)` and `CAW`. 

We would like to be able to handle all these cases.
* need to allow many combinations and then trade off evidences. For example,
corp vs. he/she
corp vs. company
prefix of the other
named entities in parenthesis often introduce abbreviations
Find clusters that typecheck.

How many clusters do we need? Worst case, every mention in its own cluster.
Since every mention can be potentially assigned to any cluster, quadratic blow-up

Would like to reduce this

 * idea1: don't allow all combinations of mentions to cluster,
   instead create a prototype cluster from each mention, and allow a mention
   only to be assigned to all prototype clusters that are somehow compatible.

 * idea2: only allow to be assigned to prototype clusters from mentions
   coming earlier in the document.

But which should be the representative mentions?


As typical for a Deepdive application, we are going to apply probabilistic inference
to determine the set of representative mentions and the links between all mentions and
their representative mentions. This requires us splitting the 
problem into two tasks: generating candidates and assigning truth values to these
candidates.

<!--
Our candidates are pairs of mentions in the text and entities in the database,
and we define a boolean random variable for each candidate to indicate if the
mention refers to the entity in the database. We thus define the following type
of variable:
-->

```
schema.variables {
    orgprotos.is_proto: Boolean
    orglinks.is_link: Boolean
}
```
<!--
For our candidate table, we choose the following schema: 

```sql
DROP TABLE IF EXISTS locations CASCADE;
CREATE TABLE locations (
        id bigint,
        mention_id varchar(100),
        sent_id int,
        mention_num int,
        mention_str varchar(100),
        w_from int,
        w_to int,
        loc_id int,
        is_correct boolean,
        features text[]
) DISTRIBUTED BY (mention_id);
```

We add one row for each combination of named entity span and entity in our 
location database. But wait – that is impossible! There are 202,055 spans and
2,139,073 geographic locations, hence 432,210,395,015 combinations.
 
This means that we would need to do probabilistic inference over more than
432 billion variables, not an easy problem.

To reduce the search space, we don't generate every possible combination of
named entity span and entry in our database, but only those that are
promising according to some heuristic.

avoid quadratic blow-up.



For simplicity, we only consider combinations for which we get an exact
string match. For example, for the mention `San Francisco` we only consider
the 30+ locations with name `San Francisco` but not any other. This may
limit our recall, since our text might contain other spellings referring
to the same entity, such as `S.F.`, `SanFran`, or `San Franzisko`. For each
entity linking problem, it is therefore important to come up with candidate
generation rules that reduce the search space but do not significantly
reduce recall.

With our heuristic, we obtain 344,806 candidates covering 51,218 unique
mentions for which we found at least one match. This means that on average
we have to disambiguate among 7 alternative entities for each mention.
-->
TODO

## Probabilistic Inference

TODO
<!--
* encourage 

To disambiguate mentions, we need to design features that allow the system
to differentially weight different mention-entity pairings. Both, information
about entities and information about the context of a mention in text may help.

Information about entities in database:

* Locations that are larger or are generally more important are more likely to
  be referenced that others. For example, locations with
  a larger population, or a country vs. a city, city vs. a town.
* Multiple locations referenced in the same document are more likely to be
  close to each other. For example, if a document contains references to
  different cities in Argentina and it also contains a mention `San Francisco`,
  then it may be more likely that this mention indeed refers to San Francisco, Córdoba
  in Argentina and not San Francisco, California.

Information about context of mention in text:

* Words appearing before or after a mention may help to determine if the mention
  refers to a location, or which location it refers to. For example, 
  a prefix `baseball stadium in` makes it more
  likely that a mention is indeed a location, that it's a city, that the city
  is in the U.S., and that the city is one of those having a baseball stadium.
* Other named entities appearing in the same sentence may help. For example, mentions
  of `Washington` are more likely to refer to the nation's capital when the
  president or Congress are named as well; conversely, they are more likely to
  refer to the state when Seattle or Mount Rainier are mentioned.

Let's now encode these intuitions as factors over our variables. In this section,
we focus on factors about entities in the database and manually assign a weight
to each factor. The following section then discusses factors about context and describes
how we can learn the weights automatically from distantly supervised annotations.

First, we would like to assign more weight to larger, more important locations.
Population would be a great attribute to use for this, but Wikidata's population
coverage is too small, so we instead use Wikidata's classification of `city`, `city with hundreds
of thousands of inhabitants`, `city with millions of inhabitants`, and `country`.
For each of these classes we create a factor of the following form:

```
# preference for cities
city {
  input_query: """
    SELECT l.id as "linking.id", l.is_correct as "linking.is_correct"
    FROM locations l, wikidata_instanceof i
    WHERE l.loc_id = i.item_id
    AND i.clazz_id = 515;
    """
  function: "IsTrue(linking.is_correct)"
  weight: 1
}
```

We give larger weights to classes of larger locations; for details see [application.conf](application.conf).

Next, we would like to give a preference to subsequently mentioned cities that
are close to each other in geographic distance.

```
# prefer if subsequently mentioned cities are within 1000km distance
consecutive_in_proximity {
  input_query: """
    SELECT l1.id as "linking1.id", l1.is_correct as "linking1.is_correct",
           l2.id as "linking2.id", l2.is_correct as "linking2.is_correct"
    FROM locations l1, locations l2,
         wikidata_coordinate_locations c1, wikidata_coordinate_locations c2
    WHERE l1.loc_id = c1.item_id
    AND l2.loc_id = c2.item_id
    AND l1.sentence_id = l2.sentence_id
    AND l2.mention_num = l1.mention_num + 1
    AND earth_distance(ll_to_earth(c1.latitude,c1.longitude), ll_to_earth(c2.latitude,c2.longitude)) < 1000;
    """
  function: "And(linking1.is_correct, linking2.is_correct)"
  weight: "3"
}
```

Note: In order to computate distances between geographic locations, you must
install the [cube](http://www.postgresql.org/docs/9.4/static/cube.html) and
[earthdistance](http://www.postgresql.org/docs/9.4/static/earthdistance.html) modules into postgresql.
See this [documentation](http://www.postgresql.org/docs/9.4/static/contrib.html) for more
information on how to install these modules.

Finally, we must ensure that the system maps each mention to at most
one location entity. We encode this constraint using a factor that gives a penalty
when two variables of the same mention have a positive boolean value:

```
one_of_n_features {
  input_query = """
    SELECT l1.id as "linking1.id", l1.is_correct as "linking1.is_correct",
           l2.id as "linking2.id", l2.is_correct as "linking2.is_correct"
    FROM locations l1, locations l2
    WHERE l1.sentence_id = l2.sentence_id
    AND l1.mention_num = l2.mention_num
    AND NOT l1.mention_id = l2.mention_id;
    """
  function: "And(linking1.is_correct, linking2.is_correct)"
  weight: -10
}
```

At this point, we have a functioning entity-linking system for locations.
Set the pipeline to `entity_features_only` in [application.conf](application.conf),
then run `./run.sh` and inspect the outputs:

```sql
SELECT mention_str, loc_id, sentence 
FROM locations_is_correct_inference l, sentences s 
WHERE l.sentence_id = s.sentence_id
AND expectation > .9 
ORDER BY random()
LIMIT 100;
```
Although there's some noise in the output, many locations are resolved correctly, for example:

```
London      |      84 | The SES is discussing the idea with the London and New York authorities .
Shanghai    |    8686 | It said the venture will be based in Shanghai and produce agents for use in hotels and industries .
Tianjin     |   11736 | China has signed a 130 mln dlr loan agreement with the World Bank to partly finance 12 new berths with an annual capacity of 6.28 mln tonnes at the 20 mln tonne a year capacity Tianjin port , the New China News Agency said .
```

You can verify the target locations by opening Wikidata's pages for [Q84](http://www.wikidata.org/wiki/Q84), [Q8686](http://www.wikidata.org/wiki/Q8686), and [Q11736](http://www.wikidata.org/wiki/Q11736) and Reuters' full articles.
-->

## Weight learning

<!--
So far, we have manually set weights for our factors based on intuitions. These weights,
however, may not be optimal and we may obtain more accurate results by learning weights
from data. Furthermore, we would like to leverage a large number of distinct features
about the context of a mention. It would be difficult or impossible to manually assign
weights to such features.

To learn weights, we must make two changes to our Deepdive application:

1. We must replace our manually set weights with `?`.

2. We must provide annotations on a subset of the variables.
 
While manually annotating data is expensive, we can write distant supervision rules
to more efficiently generate annotations.

Here are a variety of ideas for distant supervision rules:

1. annotate unambiguous locations
2. annotate locations that can be disambiguated by zip codes and phone area codes
  appearing in the same document
3. many documents contain references to companies and persons; use background
  information from Wikidata for disambiguation
4. find matches to other (non-location) Wikidata entities; if these share a relation
  with a location appearing in the same document, annotate
5. write prefix/suffix patterns that have high precision
6. meta information in the corpus allows disambiguation (eg. document tags such as `U.S. national`)

Our distant supervision rules use a combination of 1. and 5. 

We have also created an extractor that populates a table called `context_features` with
features for phrases appearing before or after a mention, and other named entities appearing
in the same sentence. These features are then added to our inference with the following factor: 

```
context_features {
  input_query = """
    SELECT l.id as "locations.id", l.is_correct as "locations.is_correct", unnest(f.features) as "locations.feature"
    FROM locations l, context_features f
    WHERE l.sentence_id = f.sentence_id
    AND l.mention_num = f.mention_num;
    """
  function: "IsTrue(locations.is_correct)"
  weight: "?(locations.feature)"
}
```

To run this enhanced entity linker, set the pipeline to `all_features` in [application.conf](application.conf),
then run `./run.sh` and inspect the outputs as described in the previous section.
-->

```sql
select i.*, o1.name, o2.name, p.expectation from orglinks_is_link_inference i, orgs o1, orgs o2, orgprotos_is_proto_inference p where i.mention_id = o1.mention_id and i.proto_mention_id = o2.mention_id and i.proto_mention_id = p.proto_mention_id order by o1.document_id, o1.sentence_num, o1.mention_num limit 100;
```


```
  mention_id   | proto_mention_id | is_link |        name         |        name         | is_proto
---------------+------------------+---------+---------------------+---------------------+----------
 10006_-1_0_2  | 10006_-1_0_2     |    0.98 | GENCORP             | GENCORP             |    0.989
 10006_0_0_1   | 10006_-1_0_2     |   0.518 | GenCorp             | GENCORP             |    0.989
 10006_0_0_1   | 10006_0_0_1      |   0.467 | GenCorp             | GenCorp             |     0.82
 10006_0_13_14 | 10006_-1_0_2     |   0.139 | Shelbyville         | GENCORP             |    0.989
 10006_0_13_14 | 10006_0_0_1      |   0.142 | Shelbyville         | GenCorp             |     0.82
 10006_0_13_14 | 10006_0_13_14    |   0.699 | Shelbyville         | Shelbyville         |    0.877
 10006_0_15_16 | 10006_0_15_16    |   0.413 | Ind.                | Ind.                |    0.595
 10006_0_15_16 | 10006_0_0_1      |   0.183 | Ind.                | GenCorp             |     0.82
 10006_0_15_16 | 10006_-1_0_2     |   0.169 | Ind.                | GENCORP             |    0.989
 10006_0_15_16 | 10006_0_13_14    |   0.208 | Ind.                | Shelbyville         |    0.877
```

You can see that mentions GENCORP (in title) and GenCorp (in first sentence) both link to GENCORP,
the highest is_link expectation for these mentions. 


## Additional Material with Ideas to Improve our System

 * Poon and Domingos. [Joint Unsupervised Coreference Resolution with Markov Logic](http://research.microsoft.com/en-us/um/people/hoifung/papers/poon08b.pdf), 2008.

  Explains how to design a factor graph for coreference resolutions that takes into account far more constraints than discussed in this tutorial.

 * Wick, Singh and McCallum. [A Discriminative Hierarchical Model for Fast Coreference at Large Scale](http://sameersingh.org/files/papers/hierar-coref-acl12.pdf), 2012.

  Explains how factor-graph based coreference resolution can be scaled to large amounts of text.

 * Lee, Chang, Peirsman, Chambers, Surdeanu, Jurafsky. [Deterministic Coreference Resolution based on entity-centric, precision-ranked rules](http://nlp.stanford.edu/software/dcoref.shtml), 2013.

  Explains the importance of many types of evidence for coreference resolution.

