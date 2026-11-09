"""Clean netflix_titles.csv and build the tables used by the SQL analysis and the dashboard.

Usage (from the repo root):
    python src/prepare_data.py                      # reads data/raw/netflix_titles.csv
    python src/prepare_data.py path/to/netflix_titles.csv

Outputs (data/processed/):
    titles.csv           one row per title, cleaned types and dates
    title_countries.csv  one row per title x country (co-productions list several countries)
    title_genres.csv     one row per title x genre label, with a merged genre family
    title_directors.csv  one row per title x director
    data_quality.json    what was cleaned and what is missing
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
from netflix_utils import LAST_FULL_YEAR, PROC, RAW, RATING_GROUP, family  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAW, "netflix_titles.csv")
raw = pd.read_csv(path)
os.makedirs(PROC, exist_ok=True)
dq = {"rows": int(len(raw)), "columns": int(raw.shape[1]), "duplicate_show_ids": int(raw["show_id"].duplicated().sum())}
dq["missing_by_column"] = {c: int(n) for c, n in raw.isna().sum().items() if n}
dq["missing_pct_by_column"] = {c: round(100 * n / len(raw), 1) for c, n in raw.isna().sum().items() if n}
# same title, type and year but different show_id (Sarkar, Tiger, Kakegurui): kept, since the file cannot show whether they are the same title
dq["repeated_title_type_year_pairs"] = int(raw.duplicated(["title", "type", "release_year"]).sum())

t = raw.copy()
for c in ["title", "director", "cast", "country", "rating", "listed_in", "description"]:
    t[c] = t[c].str.strip()
dq["date_added_with_stray_spaces"] = int((raw["date_added"].dropna() != raw["date_added"].dropna().str.strip()).sum())
t["date_added"] = pd.to_datetime(t["date_added"].str.strip(), format="%B %d, %Y", errors="raise")
t["year_added"] = t["date_added"].dt.year.astype("Int64")
t["month_added"] = t["date_added"].dt.month.astype("Int64")
dq["last_date_added"] = str(t["date_added"].max().date())

# ---- duration: movies are minutes, TV shows are seasons
mins = t["duration"].str.extract(r"^(\d+) min$")[0]
seas = t["duration"].str.extract(r"^(\d+) Seasons?$")[0]
assert (t.loc[t["type"] == "Movie", "duration"].str.endswith("min")).all()
assert (t.loc[t["type"] == "TV Show", "duration"].str.contains("Season")).all()
t["duration_min"] = pd.to_numeric(mins).astype("Int64")
t["seasons"] = pd.to_numeric(seas).astype("Int64")
t = t.drop(columns="duration")

# ---- ratings
unknown = set(t["rating"].dropna()) - set(RATING_GROUP)
assert not unknown, f"unmapped ratings {unknown}"
t["rating_group"] = t["rating"].map(RATING_GROUP).fillna("Unrated")
dq["missing_rating_set_to_unrated"] = int(t["rating"].isna().sum())

# ---- how fresh was a title when Netflix added it?
t["years_from_release_to_added"] = t["year_added"] - t["release_year"]
dq["added_before_release_year"] = int((t["years_from_release_to_added"] < 0).sum())
t["added_within_1yr_of_release"] = (t["years_from_release_to_added"] <= 1) & (t["years_from_release_to_added"].notna())
t.loc[t["year_added"].isna(), "added_within_1yr_of_release"] = pd.NA

# ---- country lists
t["primary_country"] = t["country"].str.split(",").str[0].str.strip()
t["n_countries"] = t["country"].map(lambda s: len([x for x in s.split(",") if x.strip()]) if isinstance(s, str) else 0)
cs = (t[["show_id", "country"]].dropna().assign(country=lambda d: d["country"].str.split(","))
        .explode("country"))
cs["country"] = cs["country"].str.strip()
cs = cs[cs["country"] != ""].drop_duplicates()
dq["empty_country_entries_dropped"] = int(len(t["country"].dropna()) and sum(
    1 for s in t["country"].dropna() for x in s.split(",") if not x.strip()))
dq["distinct_countries"] = int(cs["country"].nunique())

# ---- genres
gs = t[["show_id", "listed_in"]].assign(genre=lambda d: d["listed_in"].str.split(",")).explode("genre")
gs["genre"] = gs["genre"].str.strip()
gs["family"] = gs["genre"].map(family)
gs = gs[["show_id", "genre", "family"]].drop_duplicates()
dq["raw_genre_labels"] = int(gs["genre"].nunique())
dq["genre_families"] = int(gs["family"].nunique())

# ---- directors
ds = (t[["show_id", "director"]].dropna().assign(director=lambda d: d["director"].str.split(","))
        .explode("director"))
ds["director"] = ds["director"].str.strip()
ds = ds[ds["director"] != ""].drop_duplicates()
dq["distinct_directors"] = int(ds["director"].nunique())

keep = ["show_id", "type", "title", "director", "cast", "country", "primary_country", "n_countries", "date_added",
        "year_added", "month_added", "release_year", "rating", "rating_group", "duration_min", "seasons",
        "years_from_release_to_added", "added_within_1yr_of_release", "listed_in", "description"]
t = t[keep]
assert t["show_id"].is_unique and len(t) == len(raw)
assert t.loc[t["type"] == "Movie", "duration_min"].notna().all() and t.loc[t["type"] == "TV Show", "seasons"].notna().all()
dq["movies"] = int((t["type"] == "Movie").sum())
dq["tv_shows"] = int((t["type"] == "TV Show").sum())
dq["added_in_partial_year_2020"] = int((t["year_added"] > LAST_FULL_YEAR).sum())
dq["release_year_range"] = [int(t["release_year"].min()), int(t["release_year"].max())]

t.to_csv(os.path.join(PROC, "titles.csv"), index=False)
cs.to_csv(os.path.join(PROC, "title_countries.csv"), index=False)
gs.to_csv(os.path.join(PROC, "title_genres.csv"), index=False)
ds.to_csv(os.path.join(PROC, "title_directors.csv"), index=False)
with open(os.path.join(PROC, "data_quality.json"), "w") as f:
    json.dump(dq, f, indent=2)
print(json.dumps(dq, indent=2))
