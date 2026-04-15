from typing import List, Dict
from datetime import datetime, timedelta
import feedparser
import html
import re

from db import SessionLocal
from models import FeedItem

FEED_SOURCES = [
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "category": "Security",
    },
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "category": "Security",
    },
    {
        "name": "DevOps.com",
        "url": "https://devops.com/feed/",
        "category": "DevSecOps",
    },
    {
        "name": "InfoQ Cloud",
        "url": "https://feed.infoq.com/cloud-computing-architecture-design",
        "category": "Cloud",
    },
]


def clean_text(value: str, max_length: int = 280) -> str:
    if not value:
        return "No summary available."

    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_length:
        return text[: max_length - 3].rstrip() + "..."

    return text


def fetch_live_feed_items(limit_per_source: int = 3, total_limit: int = 12) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []

    for source in FEED_SOURCES:
        try:
            parsed = feedparser.parse(source["url"])

            for entry in parsed.entries[:limit_per_source]:
                link = entry.get("link", "#")
                if not link or link == "#":
                    continue

                items.append(
                    {
                        "title": clean_text(entry.get("title", "Untitled"), max_length=160),
                        "source": source["name"],
                        "category": source["category"],
                        "summary": clean_text(
                            entry.get("summary", entry.get("description", "No summary available.")),
                            max_length=320,
                        ),
                        "link": link,
                        "published_at": clean_text(
                            entry.get("published", entry.get("updated", "Unknown date")),
                            max_length=80,
                        ),
                    }
                )
        except Exception:
            continue

    return items[:total_limit]


def refresh_feed_cache(limit_per_source: int = 3, total_limit: int = 12) -> None:
    items = fetch_live_feed_items(limit_per_source=limit_per_source, total_limit=total_limit)
    if not items:
        return

    db = SessionLocal()
    try:
        for item in items:
            existing = db.query(FeedItem).filter(FeedItem.link == item["link"]).first()
            if existing:
                existing.title = item["title"]
                existing.source = item["source"]
                existing.category = item["category"]
                existing.summary = item["summary"]
                existing.published_at = item["published_at"]
                existing.fetched_at = datetime.utcnow()
            else:
                db.add(
                    FeedItem(
                        title=item["title"],
                        source=item["source"],
                        category=item["category"],
                        summary=item["summary"],
                        link=item["link"],
                        published_at=item["published_at"],
                        fetched_at=datetime.utcnow(),
                    )
                )
        db.commit()
    finally:
        db.close()


def cache_is_stale(max_age_minutes: int = 30) -> bool:
    db = SessionLocal()
    try:
        latest = db.query(FeedItem).order_by(FeedItem.fetched_at.desc()).first()
        if not latest:
            return True
        return latest.fetched_at < datetime.utcnow() - timedelta(minutes=max_age_minutes)
    finally:
        db.close()


def ensure_feed_cache(max_age_minutes: int = 30) -> None:
    if cache_is_stale(max_age_minutes=max_age_minutes):
        refresh_feed_cache()


def get_cached_feed_items(limit: int = 12) -> List[Dict[str, str]]:
    db = SessionLocal()
    try:
        rows = db.query(FeedItem).order_by(FeedItem.fetched_at.desc(), FeedItem.id.desc()).limit(limit).all()
        return [
            {
                "title": row.title,
                "source": row.source,
                "category": row.category,
                "summary": row.summary,
                "link": row.link,
                "published_at": row.published_at,
            }
            for row in rows
        ]
    finally:
        db.close()