# Tutorial: Entity Linking for Locations

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

## Preparing the Reuters dataset

We first download the Reuters corpus from [UC Irvine repository](http://archive.ics.uci.edu/ml/machine-learning-databases/reuters21578-mld/reuters21578.html).
The original data is in SGML which we convert to JSON for readability and CSV for loading into the database. The following scripts perform these steps:

    script/fetch-reuters.py
    script/get-reuters-json-csv.py

Next, we create a schema for articles in the database and load the data. Both can be done by running:

    script/load-reuters.py

The articles are stored as strings of text. To more easily identify mentions we would like
to compute word boundaries by running a tokenizer, splitting sentences, and computing part-of-speech tags. Deepdive offers the 
`nlp_extractor` for that. We can run the `nlp_extractor` on the command line or as an extraction 
step in our deepdive application. We opt for the latter and add the following extractor to `application.conf`:

```
extract_preprocess: {
  style: json_extractor
  before: psql -h ${PGHOST} -p ${PGPORT} -d ${DBNAME} -f ${APP_HOME}/schemas/sentences.sql
  input: """
         SELECT id,
           body
         FROM articles
         WHERE NOT BODY IS NULL
         ORDER BY id ASC
         """
  output_relation: sentences
  udf: ${DEEPDIVE_HOME}/examples/nlp_extractor/run.sh -k id -v body -l 100 -a "tokenize,ssplit,pos"
}
```

Note: We set `nlp_extractor` to only run its tokenize, ssplit, and pos annotators. We do not run the
parse annotator (which would normally be included), since we don't need parses and parsing requires
many hours of computation time on this corpus.

## Preparing the Wikidata dataset

We now download the Wikidata database as a [json dump](http://dumps.wikimedia.org/other/wikidata/).
Again, we have a script for that:

    script/fetch-wikidata.py

Note that Wikidata`s dumps are updated frequently, and you may need to update the path to the
latest dump inside the script. See above link for the most recent dumps.

After downloading, unpack it:

    gunzip data/wikidata/dump.json.gz

This data contains much information that we don't need. We therefore extract the information we
are interested in and store it in a format that we can load into our database system. First,
we get a list of names (and aliases) for the entities in Wikidata:

    script/get-wikidata-names.py

This will create a file `data/wikidata/names.tsv` with content as follows:

```
    1	en	label	universe
    1	en	alias	cosmos
    1	en	alias	The Universe
    1	en	alias	Space
    8	en	label	happiness
    16	en	label	highway system
    19	en	label	place of birth
    19	en	alias	birthplace
    19	en	alias	born in
    19	en	alias	POB
```

The first column is Wikidata`s unique identifier; to access information about an entity, add prefix
Q to its id and point your browser to `http://www.wikidata.org/wiki/Q[ID]`. The second column represents language, the third
indicates if a name is the canonical label, or an alias, and the fourth column is the name itself.

Our list of names contains names for all entities in Wikidata, but we would also like to know
which refer to geographic locations. To obtain geographic locations, we must analyze the relations
between entities in Wikidata. There is one entity named `geographic location` with id Q2221906.
Other entities share a relation of type `instance of` with id P31 with this entity. 

We can identify all entities that are instances of geographic locations by analyzing these relations,
but we have to be careful: There exists another type of relation called `subclass of` with id P279.
Most entities representing geographic locations are not direct instances of entity `geographic location`,
but rather of one of its subclasses such as `town`, `city`, or `country`. Even worse, geographic
locations could be instances of a subclass of a subclass of `geographic location`. To obtain all
geographic locations, we must compute the transitive closure under the subclass relation.

We first compute all instances of relations `instance_of` (P31) and `subclass_of` (P279):

    script/get-wikidata-relations.py

This creates a file `data/wikidata/relations.tsv` containing triples of entity id, relation id, and entity id.

```
    1	31	1454986
    8	31	331769
    8	31	9415
    19	31	18608756
    19	31	18608871
    19	31	18635217
    22	31	18608871
```

Next, we compute the transitive closure under `subclass_of` to obtain all instances of `geographic location` (Q2221906):

    script/get-wikidata-transitive.py

This script actually does more than that: it also computes the transitive closures for instances of `city`
(Q515), `city with hundreds of thousands of inhabitants` (Q1549591), `city with millions of inhabitants`
(Q1637706), and `country` (Q6256). As we will see, these distinctions can help us in scoring potential location disambiguations.
The output is a file `data/wikidata/transitive.tsv`:

```
    31	2221906
    33	2221906
    45	2221906
    51	2221906
    55	2221906
```

We obtain 2,907,062 instances of class `geographic location`, 36,036 of type `city`, 401 of type `city with hundreds of inhabitants` 
178 of type `city with millions of inhabitants`, and XX of type `country`.

Finally, we would like to extract latitude and longitude of locations. Again, this information will be
useful in scoring location disambiguations.

    script/get-wikidata-coordinate-locations.py 

This script creates a file `data/wikidata/coordinate-locations.tsv` with triples of entity id, latitude, longitude:

```
    31      51      5
    33      64      26
    45      38.7    -9.1833333333333
    51      -90     0
    55      52.316666666667 5.55
    62      37.766666666667 -122.43333333333
```

We obtain this information for 2,139,073 entities.

Finally, we load all data into our database system by running:

    script/load-wikidata.sh

We now have all data ready for finding location mentions and linking them to Wikidata entity ids.

## Generating Candidates

To find references to geographic locations, we first identify spans in the article text 
that may represent such references. We assume that geographic locations are typically
refered to by named entities, so we compute all sequences of consecutive tokens 
with NNP part-of-speech tags. For example, for the sentence:

    NNP  VB               NNP NNP       .
    Cook gave a speech in San Francisco . 

we would identify the two spans `Cook` and `San Francisco`. Our corpus contains
202,055 such spans.

A naive approach to our entity linking problem would simply return exact matches of these
spans with names in our database. There are two problems to this:
  
1. We may miss links, perhaps because a city has multiple names or spellings.

2. We may get multiple links, because there are multiple cities with the same name

We can tackle the first problem by including alternate names from the database.
We have therefore not only kept the label of each Wikidata entity, but also its
aliases which we can use for matching.

The more important problem, however, is the second one: There are dozens of entities
named `San Francisco`. And indeed, this is not a contrived example but a very general
problem: On average we find 7 cities with the same name, across all mentions with 
matches in our database. How do we determine which one is referenced?

As typical for a Deepdive application, we are going to apply probabilistic inference
to determine which location is most likely referenced. This requires us splitting the 
problem into two tasks: generating candidates and assigning truth values to these
candidates.

Our candidates are pairs of mentions in the text and entities in the database,
and we define a boolean random variable for each candidate to indicate if the
mention refers to the entity in the database. We thus define the following type
of variable:

```
schema.variables {
    locations.is_correct: Boolean
}
```

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

## Probabilistic Inference

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

We give larger weights to classes of larger locations; for details see (application.conf)[application.conf].

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
Try running `./run.sh` and inspecting the outputs:

```sql
SELECT mention_str, loc_id, sentence 
FROM locations_is_correct_inference l, sentences s 
WHERE l.sentence_id = s.sentence_id
AND expectation > .9 
ORDER BY random()
LIMIT 100;
```
Although there's noise in the output, many locations are resolved correctly, for example:

```
London      |      84 | The SES is discussing the idea with the London and New York authorities .
Shanghai    |    8686 | It said the venture will be based in Shanghai and produce agents for use in hotels and industries .
Tianjin     |   11736 | China has signed a 130 mln dlr loan agreement with the World Bank to partly finance 12 new berths with an annual capacity of 6.28 mln tonnes at the 20 mln tonne a year capacity Tianjin port , the New China News Agency said .
```

You can verify the target locations by opening Wikidata's pages for (Q84)[http://www.wikidata.org/wiki/Q84], (Q8686)[http://www.wikidata.org/wiki/Q8686], and (Q11736)[http://www.wikidata.org/wiki/Q11736] and Reuters' full articles.


## Weight learning

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


TODO: Precision and Recall analysis


