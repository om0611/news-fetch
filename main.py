import io
import json
import os
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"


def fetch_recent_articles(hours: int = 24) -> list[dict]:
    """
    Fetch recent articles from the RSS feed.

    Args:
        hours (int): Number of hours since the current time to fetch articles
        since.

    Returns:
        list[dict]: A list of recent articles.
    """
    feed = feedparser.parse(RSS_URL)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = []
    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if published >= cutoff:
            recent.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "published": published.strftime("%b %d, %I:%M %p UTC")
            })
    return recent


def build_txt(articles: list[dict], date_str: str) -> str:
    """
    Build a plain text digest from a list of articles.

    Args:
        articles (list[dict]): List of articles to include.
        date_str (str): Human-readable date string for the digest header.

    Returns:
        str: The full plain text content.
    """
    lines = [f"AI News Digest — {date_str}\n"]
    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. {article['title']}")
        lines.append(f"Published: {article['published']}\n")
        lines.append(article["summary"])
        lines.append(f"\nRead more: {article['link']}\n")
        lines.append("-" * 40 + "\n")
    return "\n".join(lines)


def send_digest_to_discord(text_content: str, date_str: str) -> None:
    """
    Send the digest as a plain text file attachment to Discord via webhook.

    Args:
        text_content (str): The plain text content to send.
        date_str (str): Human-readable date string used in the notification
        message.

    Returns:
        None
    """
    filename = f"ai_digest_{datetime.now().strftime('%Y-%m-%d')}.txt"
    file_obj = io.BytesIO(text_content.encode("utf-8"))

    response = requests.post(
        WEBHOOK_URL,
        data={
            "payload_json": json.dumps({
                "content": f"Your AI News Digest for {date_str} is ready!"
            })
        },
        files={
            "file": (filename, file_obj, "text/plain")
        }
    )
    response.raise_for_status()


if __name__ == "__main__":
    recent_articles = fetch_recent_articles()
    today = datetime.today().strftime("%B %d, %Y")

    if not recent_articles:
        requests.post(WEBHOOK_URL, json={"content": f"No new AI articles in the past 24 hours ({today})."})
    else:
        text_content = build_txt(recent_articles, today)
        send_digest_to_discord(text_content, today)