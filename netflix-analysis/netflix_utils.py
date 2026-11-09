"""Shared constants and helpers for the Netflix titles project (used by src/, the analysis and the dashboard)."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")

# The raw file only goes up to 18 January 2020, so 2020 is a partial year and is left out of every yearly trend.
LAST_FULL_YEAR = 2019

# 42 raw genre labels -> 23 genre families (movie and TV labels for the same genre are merged)
GENRE_FAMILY = {
    "Action & Adventure": "Action & Adventure", "TV Action & Adventure": "Action & Adventure",
    "Anime Features": "Anime", "Anime Series": "Anime",
    "British TV Shows": "International", "International Movies": "International",
    "International TV Shows": "International", "Korean TV Shows": "International",
    "Spanish-Language TV Shows": "International",
    "Children & Family Movies": "Kids & Family", "Kids' TV": "Kids & Family",
    "Teen TV Shows": "Teen TV",
    "Classic Movies": "Classic & Cult", "Cult Movies": "Classic & Cult", "Classic & Cult TV": "Classic & Cult",
    "Comedies": "Comedy", "TV Comedies": "Comedy",
    "Stand-Up Comedy": "Stand-Up & Talk", "Stand-Up Comedy & Talk Shows": "Stand-Up & Talk",
    "Crime TV Shows": "Crime",
    "Documentaries": "Documentary", "Docuseries": "Documentary",
    "Science & Nature TV": "Science & Nature",
    "Dramas": "Drama", "TV Dramas": "Drama",
    "Faith & Spirituality": "Faith & Spirituality",
    "Horror Movies": "Horror", "TV Horror": "Horror",
    "Independent Movies": "Independent",
    "LGBTQ Movies": "LGBTQ",
    "Music & Musicals": "Music & Musicals",
    "Reality TV": "Reality TV",
    "Romantic Movies": "Romance", "Romantic TV Shows": "Romance",
    "Sci-Fi & Fantasy": "Sci-Fi & Fantasy", "TV Sci-Fi & Fantasy": "Sci-Fi & Fantasy",
    "Sports Movies": "Sports",
    "Thrillers": "Thriller & Mystery", "TV Thrillers": "Thriller & Mystery", "TV Mysteries": "Thriller & Mystery",
    "Movies": "Other", "TV Shows": "Other",
}

# Content ratings -> four audience groups
RATING_GROUP = {
    "TV-MA": "Mature", "R": "Mature", "NC-17": "Mature",
    "TV-14": "Teen", "PG-13": "Teen",
    "TV-PG": "Family", "PG": "Family", "TV-G": "Family", "G": "Family",
    "TV-Y": "Kids", "TV-Y7": "Kids", "TV-Y7-FV": "Kids",
    "NR": "Unrated", "UR": "Unrated",
}
RATING_ORDER = ["Mature", "Teen", "Family", "Kids", "Unrated"]


def family(label):
    if label not in GENRE_FAMILY:
        raise KeyError(f"Unmapped genre label {label!r} - add it to GENRE_FAMILY in netflix_utils.py")
    return GENRE_FAMILY[label]
