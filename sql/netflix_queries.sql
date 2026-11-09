-- Netflix titles: SQL analysis (SQLite)
-- Tables built by src/prepare_data.py:
--   titles(show_id, type, title, director, country, primary_country, n_countries, date_added, year_added, month_added,
--          release_year, rating, rating_group, duration_min, seasons, years_from_release_to_added,
--          added_within_1yr_of_release, listed_in, description)
--   title_countries(show_id, country)      title_genres(show_id, genre, family)      title_directors(show_id, director)
-- The raw file ends on 18 January 2020, so 2020 is a partial year: yearly trends stop at 2019.
-- Years before 2015 have fewer than 100 titles each, so most trends start at 2015.

-- QUERY: Catalogue mix: movies vs TV shows
SELECT type,
       COUNT(*) AS titles,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
FROM titles
GROUP BY type
ORDER BY titles DESC;

-- QUERY: Titles added per year by type, with year-on-year growth (LAG)
WITH yearly AS (
    SELECT year_added AS year, COUNT(*) AS titles_added,
           SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,
           SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
    FROM titles
    WHERE year_added BETWEEN 2012 AND 2019
    GROUP BY year_added
)
SELECT year, movies, tv_shows, titles_added,
       ROUND(100.0 * (titles_added - LAG(titles_added) OVER (ORDER BY year)) / LAG(titles_added) OVER (ORDER BY year), 1) AS growth_pct,
       ROUND(100.0 * tv_shows / titles_added, 1) AS tv_share_pct
FROM yearly
ORDER BY year;

-- QUERY: Catalogue growth as a running total
WITH yearly AS (
    SELECT year_added AS year, COUNT(*) AS titles_added
    FROM titles
    WHERE year_added BETWEEN 2008 AND 2019
    GROUP BY year_added
)
SELECT year, titles_added,
       SUM(titles_added) OVER (ORDER BY year) AS catalogue_size
FROM yearly
ORDER BY year;

-- QUERY: Top 10 countries by number of titles
SELECT c.country,
       COUNT(*) AS titles,
       SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,
       SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(DISTINCT show_id) FROM title_countries), 1) AS pct_of_titles_with_country
FROM title_countries c
JOIN titles t USING (show_id)
GROUP BY c.country
ORDER BY titles DESC
LIMIT 10;

-- QUERY: Where new titles come from, by year added
WITH base AS (
    SELECT t.year_added AS year, c.country
    FROM title_countries c
    JOIN titles t USING (show_id)
    WHERE t.year_added BETWEEN 2015 AND 2019
)
SELECT year,
       COUNT(*) AS country_credits,
       ROUND(100.0 * SUM(CASE WHEN country = 'United States' THEN 1 ELSE 0 END) / COUNT(*), 1) AS united_states_pct,
       ROUND(100.0 * SUM(CASE WHEN country = 'India' THEN 1 ELSE 0 END) / COUNT(*), 1) AS india_pct,
       ROUND(100.0 * SUM(CASE WHEN country = 'United Kingdom' THEN 1 ELSE 0 END) / COUNT(*), 1) AS united_kingdom_pct,
       ROUND(100.0 * SUM(CASE WHEN country NOT IN ('United States', 'India', 'United Kingdom') THEN 1 ELSE 0 END) / COUNT(*), 1) AS rest_of_world_pct
FROM base
GROUP BY year
ORDER BY year;

-- QUERY: Top genre families for movies and TV shows (RANK within type)
WITH g AS (
    SELECT t.type, g.family, COUNT(DISTINCT t.show_id) AS titles
    FROM title_genres g
    JOIN titles t USING (show_id)
    WHERE g.family <> 'Other'
    GROUP BY t.type, g.family
),
ranked AS (
    SELECT type, family, titles,
           RANK() OVER (PARTITION BY type ORDER BY titles DESC) AS rank_in_type
    FROM g
)
SELECT type, rank_in_type, family, titles
FROM ranked
WHERE rank_in_type <= 6
ORDER BY type, rank_in_type;

-- QUERY: Genre families: movies vs TV shows side by side
SELECT g.family,
       COUNT(DISTINCT CASE WHEN t.type = 'Movie' THEN t.show_id END) AS movies,
       COUNT(DISTINCT CASE WHEN t.type = 'TV Show' THEN t.show_id END) AS tv_shows,
       COUNT(DISTINCT t.show_id) AS titles
FROM title_genres g
JOIN titles t USING (show_id)
WHERE g.family <> 'Other'
GROUP BY g.family
ORDER BY titles DESC;

-- QUERY: Audience rating mix by type
SELECT type, rating_group,
       COUNT(*) AS titles,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY type), 1) AS share_of_type_pct
FROM titles
GROUP BY type, rating_group
ORDER BY type, share_of_type_pct DESC;

-- QUERY: Share of mature-rated titles by year added
SELECT year_added AS year,
       COUNT(*) AS titles_added,
       ROUND(100.0 * SUM(CASE WHEN rating_group = 'Mature' THEN 1 ELSE 0 END) / COUNT(*), 1) AS mature_pct,
       ROUND(100.0 * SUM(CASE WHEN rating_group = 'Mature' AND type = 'Movie' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END), 0), 1) AS movie_mature_pct,
       ROUND(100.0 * SUM(CASE WHEN rating_group = 'Mature' AND type = 'TV Show' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END), 0), 1) AS tv_mature_pct
FROM titles
WHERE year_added BETWEEN 2015 AND 2019
GROUP BY year_added
ORDER BY year_added;

-- QUERY: Average movie length by release decade
SELECT (release_year / 10) * 10 AS decade,
       COUNT(*) AS movies,
       ROUND(AVG(duration_min), 1) AS avg_minutes,
       MIN(duration_min) AS shortest,
       MAX(duration_min) AS longest
FROM titles
WHERE type = 'Movie' AND release_year >= 1960
GROUP BY decade
ORDER BY decade;

-- QUERY: How many seasons do TV shows have?
SELECT CASE WHEN seasons >= 5 THEN '5+' ELSE CAST(seasons AS TEXT) END AS seasons,
       COUNT(*) AS shows,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
FROM titles
WHERE type = 'TV Show'
GROUP BY 1
ORDER BY 1;

-- QUERY: Is the catalogue getting newer? Share added within a year of release
SELECT year_added AS year,
       COUNT(*) AS titles_added,
       ROUND(100.0 * SUM(added_within_1yr_of_release) / COUNT(*), 1) AS added_within_1yr_pct,
       ROUND(AVG(years_from_release_to_added), 1) AS avg_years_after_release
FROM titles
WHERE year_added BETWEEN 2015 AND 2019
GROUP BY year_added
ORDER BY year_added;

-- QUERY: Busiest months for adding titles (2016-2019, RANK)
WITH m AS (
    SELECT month_added AS month, COUNT(*) AS titles_added
    FROM titles
    WHERE year_added BETWEEN 2016 AND 2019
    GROUP BY month_added
)
SELECT month, titles_added,
       ROUND(100.0 * titles_added / SUM(titles_added) OVER (), 1) AS share_pct,
       RANK() OVER (ORDER BY titles_added DESC) AS busiest_rank
FROM m
ORDER BY month;

-- QUERY: Directors with the most titles (credited directors only)
SELECT d.director,
       COUNT(*) AS titles,
       MIN(t.release_year) AS first_release,
       MAX(t.release_year) AS last_release
FROM title_directors d
JOIN titles t USING (show_id)
GROUP BY d.director
ORDER BY titles DESC, d.director
LIMIT 10;

-- QUERY: How much data is missing? (UNION ALL)
SELECT 'director' AS column_name, SUM(director IS NULL) AS missing, ROUND(100.0 * SUM(director IS NULL) / COUNT(*), 1) AS missing_pct FROM titles
UNION ALL SELECT 'cast', SUM("cast" IS NULL), ROUND(100.0 * SUM("cast" IS NULL) / COUNT(*), 1) FROM titles
UNION ALL SELECT 'country', SUM(country IS NULL), ROUND(100.0 * SUM(country IS NULL) / COUNT(*), 1) FROM titles
UNION ALL SELECT 'date_added', SUM(date_added IS NULL), ROUND(100.0 * SUM(date_added IS NULL) / COUNT(*), 1) FROM titles
UNION ALL SELECT 'rating', SUM(rating IS NULL), ROUND(100.0 * SUM(rating IS NULL) / COUNT(*), 1) FROM titles
ORDER BY missing DESC;
