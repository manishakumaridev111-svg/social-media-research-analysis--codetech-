"""
analytics.py
------------
Pure data-crunching layer. Takes raw video stat dicts (from youtube_api.py)
and produces the metrics the dashboard displays. No PyQt / UI code here,
so it can be unit-tested independently.
"""

from datetime import datetime


def _parse_date(iso_string: str):
    try:
        return datetime.strptime(iso_string[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def compute_engagement_rate(views: int, likes: int, comments: int) -> float:
    """Engagement rate (%) = (likes + comments) / views * 100. Guards against divide-by-zero."""
    if views <= 0:
        return 0.0
    return round((likes + comments) / views * 100, 2)


def enrich_videos(videos: list) -> list:
    """Add engagement_rate and parsed_date to each video dict."""
    enriched = []
    for v in videos:
        v = dict(v)  # don't mutate caller's list
        v["engagement_rate"] = compute_engagement_rate(v["views"], v["likes"], v["comments"])
        v["parsed_date"] = _parse_date(v.get("published_at", ""))
        enriched.append(v)
    return enriched


def summary_metrics(videos: list) -> dict:
    """Return channel-level rollups across the fetched video sample."""
    if not videos:
        return {
            "avg_views": 0, "avg_likes": 0, "avg_comments": 0,
            "avg_engagement_rate": 0.0, "total_views": 0,
            "total_likes": 0, "total_comments": 0, "video_sample_size": 0,
        }

    n = len(videos)
    total_views = sum(v["views"] for v in videos)
    total_likes = sum(v["likes"] for v in videos)
    total_comments = sum(v["comments"] for v in videos)

    return {
        "avg_views": round(total_views / n),
        "avg_likes": round(total_likes / n),
        "avg_comments": round(total_comments / n),
        "avg_engagement_rate": round(sum(v["engagement_rate"] for v in videos) / n, 2),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "video_sample_size": n,
    }


def top_videos_by_views(videos: list, top_n: int = 5) -> list:
    return sorted(videos, key=lambda v: v["views"], reverse=True)[:top_n]


def top_videos_by_engagement(videos: list, top_n: int = 5) -> list:
    return sorted(videos, key=lambda v: v["engagement_rate"], reverse=True)[:top_n]


def views_trend(videos: list) -> tuple:
    """
    Return (dates, views) sorted chronologically, for plotting a trend line.
    Videos without a parseable date are skipped.
    """
    dated = [v for v in videos if v.get("parsed_date") is not None]
    dated.sort(key=lambda v: v["parsed_date"])
    dates = [v["parsed_date"].strftime("%d %b") for v in dated]
    views = [v["views"] for v in dated]
    return dates, views


def reach_classification(avg_engagement_rate: float) -> str:
    """Simple qualitative label for the engagement rate, useful for a dashboard headline."""
    if avg_engagement_rate >= 8:
        return "Excellent Reach"
    elif avg_engagement_rate >= 4:
        return "Good Reach"
    elif avg_engagement_rate >= 1:
        return "Average Reach"
    else:
        return "Low Reach"
