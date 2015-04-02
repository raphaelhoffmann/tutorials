# Tutorial: Entity Linking for Locations

References to locations are ubiquitous in text, but many such references are ambiguous. For
example, Wikipedia lists [more than 30 locations](https://en.wikipedia.org/wiki/San_Francisco_(disambiguation)) named 'San Francisco', 10 songs with
that name, 2 movies, a magazine, and several other things as well.
In this tutorial, we develop a system that detects mentions of geographic locations
and links these unambiguously to a database of locations.

We start with a corpus of 20,000 news articles, the Reuters-21578 dataset, which 
represents articles that appeared on the Reuters newswire in 1987. Our goal is to identify
mentions of locations in these articles and unambiguously link them to entities in Wikidata, 
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
to compute word boundaries by running a tokenizer and splitting sentences. Deepdive offers the 
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
  udf: ${DEEPDIVE_HOME}/examples/nlp_extractor/run.sh -k id -v body -l 100 -a "tokenize,ssplit"
}
```

Note: We set `nlp_extractor` to only run its tokenize and ssplit annotators. We do not run the
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

    1	31	1454986
    8	31	331769
    8	31	9415
    19	31	18608756
    19	31	18608871
    19	31	18635217
    22	31	18608871

Next, we compute the transitive closure under `subclass_of` to obtain all instances of `geographic location` (Q2221906):

    script/get-wikidata-transitive.py

This script actually does more than that: it also computes the transitive closures for instances of `city`
(Q515), `city with hundreds of thousands of inhabitants` (Q1549591), and `city with millions of inhabitants`
(Q1637706). As we will see, these distinctions can help us in scoring potential location disambiguations.
The output is a file `data/wikidata/transitive.tsv`:

    31	2221906
    33	2221906
    45	2221906
    51	2221906
    55	2221906

Finally, we would like to extract latitude and longitude of locations. Again, this information will be
useful in scoring location disambiguations.

    script/get-wikidata-coordinate-locations.py 

This script creates a file `data/wikidata/coordinate-locations.tsv` with triples of entity id, latitude, longitude:

    31      51      5
    33      64      26
    45      38.7    -9.1833333333333
    51      -90     0
    55      52.316666666667 5.55
    62      37.766666666667 -122.43333333333


## Generating Candidates

We now have all data ready 
* candidates: all sequences of consecutive tokens with NNP part-of-speech tags
* a naive approach to linking is to find exact matches of these candidates
  with entries in our cities database
* there are two problems to this:
  1. we may miss links, perhaps because a city has multiple names or spellings,
  2. we may get multiple links, because there are multiple cities with the same name
* the first can be approached by including alternate names from the database, but
  we will ignore this problem for the purpose of this tutorial and instead focus
  on the more important one here: dealing with ambiguities
* our database contains 32 cities with the name "San Francisco". Many of these are smaller
  cities in South America. On average we find 7 cities with the same name, across all
  mentions with matches in our database.
* we model this linking problem with a boolean random variable for each combination of mention and location:

```
schema.variables {
    locations.is_correct: Boolean
}
```

* our candidate table has the following schema

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

* only relevant here is that there is one row for each combination of candidate span in the text,
  and location in our location database. 
* For tractability we generate such a candidate only if we find an exact match of span in the text and name of a location in the the database.

## Distant Supervision

* map unambiguous cities (where we only have one match)
* map cities which are both the largest and are located in the US
* add as additional rows

## Adding Features

* need to design features that allow the system to differentially weight location matches for a given mention
* for each country, we add feature `country_COUNTRY` 
* for each other candidate in same sentence, we add `near_OTHERCANDIDATE`
* for each city that has the highest population of cities with the same name, we add `is_most_populous`

* For above candidate, we get the following entries in our features table, note that the features here are sensitive to both the mention and the target location.

```
     1 | 1199_34_35_4413621 |    1199 |           0 | Washington       |     34 |   35 |  4413621 |            | {country_US}
     2 | 1284_9_10_4164138  |    1284 |           0 | Miami            |      9 |   10 |  4164138 |            | {is_most_populous,country_US,near_Maggot_Mile,near_Las_Vegas}
     3 | 1284_9_10_4164138  |    1284 |           0 | Miami            |      9 |   10 |  4164138 |            | {is_most_populous,country_US,near_Maggot_Mile,near_Las_Vegas}
     4 | 2119_8_10_5368361  |    2119 |           0 | Los Angeles      |      8 |   10 |  5368361 |            | {is_most_populous,country_US}
     5 | 2119_8_10_5368361  |    2119 |           0 | Los Angeles      |      8 |   10 |  5368361 | t          | {is_most_populous,country_US}
     6 | 487_17_18_5126705  |     487 |           0 | Mexico           |     17 |   18 |  5126705 |            | {country_US}
     7 | 487_17_18_5126705  |     487 |           0 | Mexico           |     17 |   18 |  5126705 | t          | {country_US}
     8 | 965_17_19_1690011  |     965 |           0 | San Francisco    |     17 |   19 |  1690011 |            | {country_PH}
     9 | 965_17_19_1690011  |     965 |           0 | San Francisco    |     17 |   19 |  1690011 |            | {country_PH}
    10 | 277_31_33_3669860  |     277 |           0 | San Francisco    |     31 |   33 |  3669860 |            | {country_CO}
```

## Factors

* we would like three kinds of factors
* first, we want to have a logistic regression classifier that uses the features we have generates above

```
    pairs_features {
      input_query = """
        SELECT l.id as "locations.id", l.is_correct as "locations.is_correct", unnest(l.features) as "locations.feature"
        FROM locations l;
           """
      function: "IsTrue(locations.is_correct)"
      weight: "?(locations.feature)"
    }
```
* second, we want to ensure that we predict only one location for any given mention 
```
    one_of_n_features {
      input_query = """
        SELECT l1.id as "linking1.id", l1.is_correct as "linking1.is_correct",
               l2.id as "linking2.id", l2.is_correct as "linking2.is_correct"
        FROM locations l1, locations l2
        WHERE l1.sent_id = l2.sent_id
        AND l1.mention_num = l2.mention_num
        AND NOT l1.mention_id = l2.mention_id;
         """
      function: "And(linking1.is_correct, linking2.is_correct)"
      weight: -10
    }
```

* third, we want to consider the predictions in the neighborhood, for example prefering consecutive links to locations of the same country
```
    consecutive_in_same_country {
      input_query: """
        SELECT l1.id as "linking1.id", l1.is_correct as "linking1.is_correct",
               l2.id as "linking2.id", l2.is_correct as "linking2.is_correct"
        FROM locations l1, locations l2,
             cities1000 c1, cities1000 c2
        WHERE l1.loc_id = c1.geonameid
        AND l2.loc_id = c2.geonameid
        AND l1.sent_id = l2.sent_id
        AND l2.mention_num = l1.mention_num + 1
        AND c1.country_code = c2.country_code
        """
      function: "And(linking1.is_correct, linking2.is_correct)"
      weight: "5"
    }
```
 * TODO: use longitude/latitude
