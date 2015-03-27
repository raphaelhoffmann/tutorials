# Entity Linking for Locations

* start with set of news articles
* goal is to link cities to the cities1000 database from geonames.org
  (about 150,000 cities worldwide with names, alternate names, populations, and more)

## Generating Candidates

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
ROP TABLE IF EXISTS locations CASCADE;
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
