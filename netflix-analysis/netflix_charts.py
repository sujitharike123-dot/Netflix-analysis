"""Chart functions shared by the analysis script (README figures) and the Streamlit dashboard.

Design rules: one accent colour (blue) with gray for context, categorical colours in a fixed order (blue, orange,
aqua), thin marks, hairline gridlines, no dual axes, a legend whenever there are two or more series, text in ink
colours. Every function takes a DataFrame and returns a matplotlib Figure.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, CONTEXT = "#e1e0d9", "#c3c2b7", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _base(figsize=(8, 4.2), horizontal_grid=False):
    fig, ax = plt.subplots(figsize=figsize, dpi=110)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    (ax.xaxis if horizontal_grid else ax.yaxis).grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def _titles(ax, title, subtitle=None):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=INK, pad=26 if subtitle else 12)
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=9, color=INK2, va="bottom")


def _done(fig):
    fig.tight_layout()
    return fig


def _legend(ax, **kw):
    leg = ax.legend(frameon=False, fontsize=9, labelcolor=INK2, **kw)
    return leg


def save(fig, path):
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def chart_titles_added(df):
    """df: year, movies, tv_shows (grouped bars, one pair per year)."""
    fig, ax = _base()
    x = np.arange(len(df))
    w = 0.38
    ax.bar(x - w / 2, df["movies"], w, color=BLUE, label="Movies", zorder=3)
    ax.bar(x + w / 2, df["tv_shows"], w, color=ORANGE, label="TV shows", zorder=3)
    for xi, v in zip(x - w / 2, df["movies"]):
        ax.text(xi, v + 25, f"{int(v):,}", ha="center", fontsize=8, color=INK2)
    for xi, v in zip(x + w / 2, df["tv_shows"]):
        ax.text(xi, v + 25, f"{int(v):,}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(df["year"].astype(int))
    ax.set_ylim(0, df[["movies", "tv_shows"]].to_numpy().max() * 1.15)
    _legend(ax, loc="upper left")
    _titles(ax, "Titles added to Netflix per year", "Titles still in the catalogue in January 2020, by the year they were added")
    return _done(fig)


def chart_top_countries(df):
    """df: country, movies, tv_shows, sorted best-first (stacked horizontal bars)."""
    d = df.iloc[::-1]
    fig, ax = _base(figsize=(8, 4.4), horizontal_grid=True)
    ax.yaxis.grid(False)
    y = np.arange(len(d))
    ax.barh(y, d["movies"], 0.62, color=BLUE, label="Movies", zorder=3)
    ax.barh(y, d["tv_shows"], 0.62, left=d["movies"], color=ORANGE, label="TV shows", zorder=3)
    for yi, tot in zip(y, d["movies"] + d["tv_shows"]):
        ax.text(tot, yi, f"  {int(tot):,}", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(d["country"], fontsize=9)
    ax.set_xlim(0, (d["movies"] + d["tv_shows"]).max() * 1.12)
    _legend(ax, loc="lower right")
    _titles(ax, "Top 10 countries by number of titles", "A co-production counts once for each country")
    return _done(fig)


def chart_country_share(df):
    """df: year, united_states_pct, india_pct, united_kingdom_pct, rest_of_world_pct."""
    fig, ax = _base()
    series = [("united_states_pct", "United States", BLUE), ("india_pct", "India", ORANGE),
              ("united_kingdom_pct", "United Kingdom", AQUA), ("rest_of_world_pct", "Rest of world", MUTED)]
    for col, name, colr in series:
        ax.plot(df["year"], df[col], color=colr, linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=name, zorder=3,
                linestyle="--" if name == "Rest of world" else "-")
        nudge = {"india_pct": 1.3, "united_kingdom_pct": -1.3}.get(col, 0)
        ax.text(df["year"].iloc[-1] + 0.08, df[col].iloc[-1] + nudge, f"{df[col].iloc[-1]:.0f}%", va="center", fontsize=8.5, color=INK2)
    ax.set_xticks(df["year"])
    ax.set_xticklabels(df["year"].astype(int))
    ax.set_xlim(df["year"].min() - 0.2, df["year"].max() + 0.5)
    ax.set_ylim(0, 62)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    _legend(ax, loc="upper right", ncol=2)
    _titles(ax, "Where each year's new titles come from", "Share of country credits among titles added that year")
    return _done(fig)


def chart_genres(df, n=10):
    """df: family, movies, tv_shows, titles (sorted by titles)."""
    d = df.head(n).iloc[::-1]
    fig, ax = _base(figsize=(8, 5), horizontal_grid=True)
    ax.yaxis.grid(False)
    y = np.arange(len(d))
    h = 0.38
    ax.barh(y + h / 2, d["movies"], h, color=BLUE, label="Movies", zorder=3)
    ax.barh(y - h / 2, d["tv_shows"], h, color=ORANGE, label="TV shows", zorder=3)
    for yi, v in zip(y + h / 2, d["movies"]):
        if v:
            ax.text(v, yi, f" {int(v):,}", va="center", fontsize=8, color=INK2)
    for yi, v in zip(y - h / 2, d["tv_shows"]):
        if v:
            ax.text(v, yi, f" {int(v):,}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels(d["family"], fontsize=9)
    ax.set_xlim(0, d[["movies", "tv_shows"]].to_numpy().max() * 1.12)
    _legend(ax, loc="lower right")
    _titles(ax, "Most common genres", "Titles can carry several genres, so bars add up to more than the catalogue")
    return _done(fig)


def chart_rating_mix(df):
    """df: type, rating_group, share_of_type_pct."""
    order = ["Mature", "Teen", "Family", "Kids", "Unrated"]
    fig, ax = _base()
    x = np.arange(len(order))
    w = 0.38
    for off, typ, colr, lab in [(-w / 2, "Movie", BLUE, "Movies"), (w / 2, "TV Show", ORANGE, "TV shows")]:
        s = df[df["type"] == typ].set_index("rating_group")["share_of_type_pct"].reindex(order).fillna(0)
        ax.bar(x + off, s.values, w, color=colr, label=lab, zorder=3)
        for xi, v in zip(x + off, s.values):
            ax.text(xi, v + 0.8, f"{v:.0f}%", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_ylim(0, 52)
    _legend(ax, loc="upper right")
    _titles(ax, "Who the catalogue is rated for", "Mature = TV-MA, R, NC-17. Teen = TV-14, PG-13. Family = TV-PG, PG, TV-G, G. Kids = TV-Y, TV-Y7")
    return _done(fig)


def chart_mature_by_year(df):
    """df: year, movie_mature_pct, tv_mature_pct."""
    fig, ax = _base()
    for col, name, colr in [("movie_mature_pct", "Movies", BLUE), ("tv_mature_pct", "TV shows", ORANGE)]:
        ax.plot(df["year"], df[col], color=colr, linewidth=2, marker="o", markersize=5, markeredgecolor=SURFACE,
                markeredgewidth=1.5, label=name, zorder=3)
        ax.text(df["year"].iloc[-1] + 0.08, df[col].iloc[-1], f"{df[col].iloc[-1]:.0f}%", va="center", fontsize=8.5, color=INK2)
    ax.set_xticks(df["year"])
    ax.set_xticklabels(df["year"].astype(int))
    ax.set_xlim(df["year"].min() - 0.2, df["year"].max() + 0.5)
    ax.set_ylim(0, 60)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    _legend(ax, loc="upper left")
    _titles(ax, "Mature-rated share of each year's new titles", "TV-MA, R or NC-17")
    return _done(fig)


def chart_movie_length(df):
    """df: decade, avg_minutes, movies."""
    d = df[(df["decade"] >= 1970) & (df["decade"] <= 2010)]
    fig, ax = _base()
    labels = [f"{int(dec)}s\n{int(n):,} movies" for dec, n in zip(d["decade"], d["movies"])]
    cols = [BLUE if dec == 2010 else CONTEXT for dec in d["decade"]]
    ax.bar(labels, d["avg_minutes"], 0.62, color=cols, zorder=3)
    for i, v in enumerate(d["avg_minutes"]):
        ax.text(i, v + 1.5, f"{v:.0f} min", ha="center", fontsize=8.5, color=INK2)
    ax.set_ylim(0, 130)
    _titles(ax, "Average movie length by release decade", "The 2010s include many short stand-up specials (about 67 minutes on average)")
    return _done(fig)


def chart_seasons(df):
    """df: seasons (label), share_pct."""
    fig, ax = _base()
    cols = [BLUE if s == "1" else CONTEXT for s in df["seasons"].astype(str).str.replace(".0", "", regex=False)]
    labels = df["seasons"].astype(str).str.replace(".0", "", regex=False)
    ax.bar(labels, df["share_pct"], 0.62, color=cols, zorder=3)
    for i, v in enumerate(df["share_pct"]):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9, color=INK2)
    ax.set_xlabel("Seasons", color=INK2, fontsize=9)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_ylim(0, 78)
    _titles(ax, "Most TV shows have a single season", "Share of the 1,969 TV shows by number of seasons")
    return _done(fig)


def chart_freshness(df):
    """df: year, added_within_1yr_pct."""
    fig, ax = _base()
    ax.plot(df["year"], df["added_within_1yr_pct"], color=BLUE, linewidth=2, marker="o", markersize=5,
            markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
    for yr, v in zip(df["year"], df["added_within_1yr_pct"]):
        ax.text(yr, v + 3, f"{v:.0f}%", ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(df["year"])
    ax.set_xticklabels(df["year"].astype(int))
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    _titles(ax, "Fewer of Netflix's additions are recent releases", "Share of titles added within a year of their release year")
    return _done(fig)


def chart_months(df):
    """df: month (1-12), share_pct."""
    fig, ax = _base()
    top3 = set(df.nlargest(3, "share_pct")["month"])
    cols = [BLUE if m in top3 else CONTEXT for m in df["month"]]
    ax.bar([MONTHS[int(m) - 1] for m in df["month"]], df["share_pct"], 0.62, color=cols, zorder=3)
    for i, v in enumerate(df["share_pct"]):
        ax.text(i, v + 0.2, f"{v:.1f}%", ha="center", fontsize=8, color=INK2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.set_ylim(0, 13.5)
    _titles(ax, "Titles added by month of the year", "Share of titles added in 2016-2019; the three busiest months are highlighted")
    return _done(fig)
