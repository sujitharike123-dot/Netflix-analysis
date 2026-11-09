"""Netflix Titles dashboard (Streamlit).

Run locally:   streamlit run app.py
Data:          data/processed/*.csv  (built by `python src/prepare_data.py`; committed so the app deploys as-is)
"""
import os

import numpy as np
import pandas as pd
import streamlit as st

import netflix_charts as ch
from netflix_utils import LAST_FULL_YEAR, PROC, RATING_ORDER

st.set_page_config(page_title="Netflix Titles Analysis", page_icon=":clapper:", layout="wide")


@st.cache_data
def load():
    titles = pd.read_csv(os.path.join(PROC, "titles.csv"))
    countries = pd.read_csv(os.path.join(PROC, "title_countries.csv"))
    genres = pd.read_csv(os.path.join(PROC, "title_genres.csv"))
    return titles, countries, genres


titles, countries, genres = load()

# ----------------------------------------------------------------------------- sidebar
st.sidebar.title("Netflix Titles")
st.sidebar.caption("6,234 movies and TV shows on Netflix in January 2020 (public Kaggle dataset). "
                   "Cleaned with Pandas, analysed with SQL.")
y0, y1 = st.sidebar.slider("Year added to Netflix", 2008, LAST_FULL_YEAR, (2015, LAST_FULL_YEAR))
st.sidebar.markdown("The year filter applies to every tab. The data stops on 18 January 2020, so 2020 is left out. "
                    "Years before 2015 have fewer than 100 titles each.")
st.sidebar.markdown("**Note.** This is a snapshot of what was on Netflix in January 2020. Titles that were added and "
                    "later removed are not in it, so earlier years look smaller than they were.")

t = titles[titles["year_added"].between(y0, y1)]
ids = set(t["show_id"])
tc = countries[countries["show_id"].isin(ids)]
tg = genres[genres["show_id"].isin(ids)]


def show(fig):
    st.pyplot(fig, use_container_width=True)


st.title("Netflix Titles Analysis")
tab_over, tab_ctry, tab_genre, tab_content, tab_find = st.tabs(
    ["Overview", "Countries", "Genres & ratings", "Content", "Find a title"])

# ============================================================================ overview
with tab_over:
    if len(t) == 0:
        st.info("No titles in this range.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Titles added", f"{len(t):,}")
        c2.metric("Movies", f"{100 * (t['type'] == 'Movie').mean():.0f}%")
        c3.metric("Countries represented", f"{tc['country'].nunique()}")
        c4.metric("Mature-rated", f"{100 * (t['rating_group'] == 'Mature').mean():.0f}%")
        st.markdown("**What the data says.** Netflix's catalogue grew about five times between 2016 and 2019 additions "
                    "(456 to 2,349 titles a year in this snapshot). Roughly two thirds of titles are movies, the US supplies the "
                    "most titles, India is second, and the share of mature-rated additions rose from 24% in 2015 to 43% in 2019. "
                    "The full write-up is in the README.")
        yr = (t.groupby("year_added").agg(movies=("type", lambda s: (s == "Movie").sum()),
                                          tv_shows=("type", lambda s: (s == "TV Show").sum())).reset_index()
              .rename(columns={"year_added": "year"}))
        a, b = st.columns(2)
        with a:
            show(ch.chart_titles_added(yr))
        with b:
            m = t.groupby("month_added").size().reset_index(name="n")
            m["share_pct"] = 100 * m["n"] / m["n"].sum()
            show(ch.chart_months(m.rename(columns={"month_added": "month"})))

# ============================================================================ countries
with tab_ctry:
    if len(tc) == 0:
        st.info("No titles with a country in this range.")
    else:
        n = st.slider("Number of countries to show", 5, 15, 10)
        j = tc.merge(t[["show_id", "type"]], on="show_id")
        top = (j.groupby("country").agg(movies=("type", lambda s: (s == "Movie").sum()),
                                        tv_shows=("type", lambda s: (s == "TV Show").sum())).reset_index())
        top["titles"] = top["movies"] + top["tv_shows"]
        top = top.sort_values("titles", ascending=False).head(n)
        a, b = st.columns(2)
        with a:
            show(ch.chart_top_countries(top))
        with b:
            if y1 > y0:
                jj = tc.merge(t[["show_id", "year_added"]], on="show_id")
                rows = []
                for yr_, g in jj.groupby("year_added"):
                    k = len(g)
                    rows.append({"year": yr_,
                                 "united_states_pct": 100 * (g["country"] == "United States").sum() / k,
                                 "india_pct": 100 * (g["country"] == "India").sum() / k,
                                 "united_kingdom_pct": 100 * (g["country"] == "United Kingdom").sum() / k,
                                 "rest_of_world_pct": 100 * (~g["country"].isin(["United States", "India", "United Kingdom"])).sum() / k})
                show(ch.chart_country_share(pd.DataFrame(rows)))
            else:
                st.info("Pick two or more years to see the trend.")
        st.caption(f"{t['country'].isna().sum()} of {len(t)} titles in this range have no country listed.")

# ============================================================================ genres & ratings
with tab_genre:
    if len(t) == 0:
        st.info("No titles in this range.")
    else:
        gg = tg[tg["family"] != "Other"].merge(t[["show_id", "type"]], on="show_id")
        gtab = (gg.assign(m=(gg["type"] == "Movie"), v=(gg["type"] == "TV Show")).groupby("family")
                  .agg(movies=("m", "sum"), tv_shows=("v", "sum")).reset_index())
        gtab["titles"] = gtab["movies"] + gtab["tv_shows"]
        gtab = gtab.sort_values("titles", ascending=False)
        a, b = st.columns(2)
        with a:
            show(ch.chart_genres(gtab))
        with b:
            rm = t.groupby(["type", "rating_group"]).size().reset_index(name="n")
            rm["share_of_type_pct"] = 100 * rm["n"] / rm.groupby("type")["n"].transform("sum")
            show(ch.chart_rating_mix(rm))
        if y1 > y0:
            mt = (t.groupby("year_added").apply(lambda g: pd.Series({
                "movie_mature_pct": 100 * ((g["type"] == "Movie") & (g["rating_group"] == "Mature")).sum() / max((g["type"] == "Movie").sum(), 1),
                "tv_mature_pct": 100 * ((g["type"] == "TV Show") & (g["rating_group"] == "Mature")).sum() / max((g["type"] == "TV Show").sum(), 1)}))
                  .reset_index().rename(columns={"year_added": "year"}))
            show(ch.chart_mature_by_year(mt))

# ============================================================================ content
with tab_content:
    mv = titles[(titles["type"] == "Movie")]
    dec = mv[mv["release_year"] >= 1970].assign(decade=lambda d: (d["release_year"] // 10) * 10)
    dec = dec.groupby("decade").agg(movies=("title", "size"), avg_minutes=("duration_min", "mean")).reset_index()
    a, b = st.columns(2)
    with a:
        show(ch.chart_movie_length(dec))
        st.caption("All movies in the dataset, not filtered by year added.")
    with b:
        sh = titles[titles["type"] == "TV Show"].copy()
        sh["bucket"] = np.where(sh["seasons"] >= 5, "5+", sh["seasons"].astype("Int64").astype(str))
        se = sh.groupby("bucket").size().reset_index(name="shows").sort_values("bucket")
        se["share_pct"] = 100 * se["shows"] / se["shows"].sum()
        show(ch.chart_seasons(se.rename(columns={"bucket": "seasons"})))
        st.caption("All TV shows in the dataset, not filtered by year added.")
    fr = (titles[titles["year_added"].between(max(y0, 2015), y1)].groupby("year_added")["added_within_1yr_of_release"]
          .agg(lambda s: 100 * s.astype(float).mean()).reset_index()
          .rename(columns={"year_added": "year", "added_within_1yr_of_release": "added_within_1yr_pct"}))
    if len(fr) > 1:
        show(ch.chart_freshness(fr))
    else:
        st.info("Pick a range of two or more years from 2015 onwards to see how fresh the additions are.")

# ============================================================================ explorer
with tab_find:
    st.markdown("Search the titles added in the selected years.")
    c1, c2, c3, c4 = st.columns(4)
    kind = c1.selectbox("Type", ["All", "Movie", "TV Show"])
    fam = c2.selectbox("Genre", ["All"] + sorted(set(genres["family"]) - {"Other"}))
    ctry_opts = ["All"] + countries["country"].value_counts().head(25).index.tolist()
    ctry = c3.selectbox("Country", ctry_opts)
    rate = c4.selectbox("Rating group", ["All"] + RATING_ORDER)
    text = st.text_input("Search title, cast, director or description")
    r = t
    if kind != "All":
        r = r[r["type"] == kind]
    if fam != "All":
        r = r[r["show_id"].isin(genres[genres["family"] == fam]["show_id"])]
    if ctry != "All":
        r = r[r["show_id"].isin(countries[countries["country"] == ctry]["show_id"])]
    if rate != "All":
        r = r[r["rating_group"] == rate]
    if text.strip():
        s = text.strip()
        hit = np.zeros(len(r), dtype=bool)
        for col in ["title", "cast", "director", "description"]:
            hit |= r[col].fillna("").str.contains(s, case=False, regex=False).to_numpy()
        r = r[hit]
    st.write(f"{len(r):,} titles match.")
    if len(r):
        view = r[["title", "type", "country", "year_added", "release_year", "rating", "listed_in"]].head(300)
        st.dataframe(view.rename(columns={"year_added": "added", "release_year": "released", "listed_in": "genres"}),
                     use_container_width=True, hide_index=True)
        if len(r) > 300:
            st.caption("Showing the first 300 matches. Narrow the search to see more.")
