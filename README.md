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
* we model this linking problem with a random variable for each mention;
  range is the entries in our database:

```json
schema.variables {
    locations.value: Categorical(144346)
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
        value int
) DISTRIBUTED BY (mention_id);
```

* only relevant here is that there is one row for each candidate span in the text
  and that the output variable `value` ranges over the entries in our database

## Distant Supervision

* map unambiguous cities (where we only have one match)
* map cities which are both the largest and are located in the US
* add as additional rows

```
     id | mention_id | sent_id | mention_num | mention_str | w_from | w_to | value
    ----+------------+---------+-------------+-------------+--------+------+--------
     11 | 3610_17_18 |    3610 |           0 | Oakland     |     17 |   18 |
     36 | 3610_17_18 |    3610 |           0 | Oakland     |     17 |   18 | 139598
     (2 rows)
```

## Adding Features

* need to design features that allow the system to weight matches for a location
  differently
* we only want to generate features that are relevant to a given candidate
* we create a features table with the following schema

```sql
DROP TABLE IF EXISTS locations_features CASCADE;
CREATE TABLE locations_features (
        mention_id varchar(100),
        loc_id int,
        feature varchar(100)
) DISTRIBUTED BY (mention_id);
```

* for each country, we add feature `country_COUNTRY` 
* for each other candidate in same sentence, we add `near_OTHERCANDIDATE`
* for each city that has the highest population of cities with the same name, we add `is_most_populous`

* For above candidate, we get the following entries in our features table, note that the features here are sensitive to both the mention and the target location.

```
     mention_id | loc_id |     feature
    ------------+--------+------------------
     3610_17_18 | 127028 | country_US
     3610_17_18 | 127028 | near_Marina
     3610_17_18 | 128997 | country_US
     3610_17_18 | 129336 | country_US
     3610_17_18 | 130705 | country_US
     3610_17_18 | 131076 | country_US
     3610_17_18 | 131364 | country_US
     3610_17_18 | 133212 | country_US
     3610_17_18 | 133213 | country_US
     3610_17_18 | 134518 | country_US
     3610_17_18 | 135549 | country_US
     3610_17_18 | 135987 | country_US
     3610_17_18 | 137938 | country_US
     3610_17_18 | 137939 | country_US
     3610_17_18 | 139598 | is_most_populous
     3610_17_18 | 139598 | country_US
     (16 rows)
```

## Factors

* with our factors we capture

```
    locations_features {
      input_query = """
        SELECT "locations.id", "locations.value", null as "features.id", "features.loc_id", "features.feature"
        FROM (
          SELECT c.id as "locations.id", c.value as "locations.value", f.loc_id as "features.loc_id", f.feature as "features.feature"
          FROM
            locations c,
            locations_features f
          WHERE
            c.mention_id = f.mention_id
       ) s;
           """
      function: "Equal(locations.value, features.loc_id)"
      weight: "?(features.feature)"
    }

    factor_linear_chain_crf {
      input_query: """
        SELECT l1.id as "locations.l1.id", l2.id as "locations.l2.id",
           l1.value as "locations.l1.value", l2.value as "locations.l2.value"
        FROM locations l1, locations l2
        WHERE l1.sent_id = l2.sent_id AND l2.mention_num = l1.mention_num + 1"""
      function: "Multinomial(locations.l1.value, locations.l2.value)"
      weight: "?"
    }
```

