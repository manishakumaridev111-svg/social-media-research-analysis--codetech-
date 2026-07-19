"""
youtube_api.py
--------------
Thin wrapper around the YouTube Data API v3 (REST) using the `requests`
library. No heavy Google client library needed.

All functions raise `YouTubeAPIError` on failure with a human-readable
message so the UI layer can show a clean error dialog instead of a
raw traceback.
"""

import requests

BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Raised whenever the YouTube API returns an error or bad input is given."""
    pass


def _get(endpoint: str, params: dict) -> dict:
    """Internal helper: perform a GET request and raise a clean error on failure."""
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise YouTubeAPIError(f"Network error while calling YouTube API: {exc}")

    if response.status_code != 200:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        raise YouTubeAPIError(f"YouTube API error ({response.status_code}): {message}")

    return response.json()


def resolve_channel_id(api_key: str, identifier: str) -> str:
    """
    Resolve a channel handle (e.g. '@MrBeast'), custom URL name, or raw
    channel ID into a canonical channel ID (starts with 'UC...').
    """
    identifier = identifier.strip()

    # Already a channel ID
    if identifier.startswith("UC") and len(identifier) == 24:
        return identifier

    # Handle style (@something) - supported via forHandle param
    handle = identifier if identifier.startswith("@") else f"@{identifier}"
    data = _get("channels", {
        "part": "id",
        "forHandle": handle,
        "key": api_key,
    })
    items = data.get("items", [])
    if items:
        return items[0]["id"]

    # Fallback: search by name
    data = _get("search", {
        "part": "snippet",
        "q": identifier,
        "type": "channel",
        "maxResults": 1,
        "key": api_key,
    })
    items = data.get("items", [])
    if items:
        return items[0]["snippet"]["channelId"]

    raise YouTubeAPIError(f"Could not find a channel matching '{identifier}'.")


def get_channel_stats(api_key: str, channel_id: str) -> dict:
    """Return channel-level stats: title, subscribers, total views, video count, uploads playlist."""
    data = _get("channels", {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
        "key": api_key,
    })
    items = data.get("items", [])
    if not items:
        raise YouTubeAPIError("Channel not found.")

    item = items[0]
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})
    uploads_playlist = item["contentDetails"]["relatedPlaylists"]["uploads"]

    return {
        "title": snippet.get("title", "Unknown"),
        "description": snippet.get("description", ""),
        "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "uploads_playlist": uploads_playlist,
    }


def get_recent_video_ids(api_key: str, uploads_playlist: str, max_results: int = 25) -> list:
    """Return the most recent video IDs from a channel's uploads playlist."""
    video_ids = []
    page_token = None

    while len(video_ids) < max_results:
        params = {
            "part": "contentDetails",
            "playlistId": uploads_playlist,
            "maxResults": min(50, max_results - len(video_ids)),
            "key": api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        data = _get("playlistItems", params)
        for item in data.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return video_ids[:max_results]


def get_video_stats(api_key: str, video_ids: list) -> list:
    """
    Return per-video stats for a list of video IDs.
    Batches requests in chunks of 50 (API limit per call).
    """
    results = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        data = _get("videos", {
            "part": "snippet,statistics",
            "id": ",".join(chunk),
            "key": api_key,
        })
        for item in data.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            results.append({
                "video_id": item["id"],
                "title": snippet.get("title", "Untitled"),
                "published_at": snippet.get("publishedAt", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })
    return results
