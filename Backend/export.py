"""
export.py
---------
Handles saving analysis results to disk: CSV (raw video data) and
PDF (readable summary report). Uses reportlab for the PDF since it's
lightweight and doesn't need a browser/HTML renderer.
"""

import csv
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def export_csv(videos: list, folder: str, channel_title: str) -> str:
    os.makedirs(folder, exist_ok=True)
    safe_name = "".join(c for c in channel_title if c.isalnum() or c in " _-").strip()
    filename = f"{safe_name}_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(folder, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Published", "Views", "Likes", "Comments", "Engagement Rate (%)"])
        for v in videos:
            writer.writerow([
                v.get("title", ""),
                v.get("published_at", "")[:10],
                v.get("views", 0),
                v.get("likes", 0),
                v.get("comments", 0),
                v.get("engagement_rate", 0.0),
            ])
    return path


def export_pdf(channel_stats: dict, summary: dict, top_videos: list, reach_label: str,
                folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    safe_name = "".join(c for c in channel_stats.get("title", "channel") if c.isalnum() or c in " _-").strip()
    filename = f"{safe_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(folder, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 2 * cm

    def line(text, size=11, gap=0.7 * cm, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(2 * cm, y, text)
        y -= gap

    line("Social Media Reach Analysis Report", size=16, bold=True, gap=1 * cm)
    line(f"Channel: {channel_stats.get('title', 'N/A')}", size=13, bold=True)
    line(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
    line(" ")

    line("Channel Overview", size=13, bold=True)
    line(f"Subscribers: {channel_stats.get('subscribers', 0):,}")
    line(f"Total Channel Views: {channel_stats.get('total_views', 0):,}")
    line(f"Total Videos on Channel: {channel_stats.get('video_count', 0):,}")
    line(" ")

    line(f"Reach Classification: {reach_label}", size=13, bold=True)
    line(" ")

    line(f"Analysis Sample: {summary.get('video_sample_size', 0)} recent videos", size=13, bold=True)
    line(f"Average Views per Video: {summary.get('avg_views', 0):,}")
    line(f"Average Likes per Video: {summary.get('avg_likes', 0):,}")
    line(f"Average Comments per Video: {summary.get('avg_comments', 0):,}")
    line(f"Average Engagement Rate: {summary.get('avg_engagement_rate', 0)}%")
    line(" ")

    line("Top Performing Videos (by Views)", size=13, bold=True)
    for i, v in enumerate(top_videos, start=1):
        title = v.get("title", "")[:65]
        line(f"{i}. {title}", size=10)
        line(f"    Views: {v.get('views', 0):,}  |  Likes: {v.get('likes', 0):,}  |  "
             f"Comments: {v.get('comments', 0):,}  |  Engagement: {v.get('engagement_rate', 0)}%",
             size=9, gap=0.6 * cm)
        if y < 3 * cm:
            c.showPage()
            y = height - 2 * cm

    c.save()
    return path
