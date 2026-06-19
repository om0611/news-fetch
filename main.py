import io
import json
import os
from datetime import date, datetime, timedelta, UTC

import feedparser
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RSS_URL = "https://techcrunch.com/category/artificial-intelligence/feed/"


def get_entry_published_date(entry) -> date | None:
    """
    Return the UTC calendar date of an RSS entry, or None if unavailable.

    Args:
        entry (feedparser.Entry): The RSS entry to parse.

    Returns:
        date | None: The UTC calendar date of the entry, or None if unavailable.
    """
    field = "published_parsed"
    parsed = entry.get(field)
    if parsed:
        return date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday)
    return None


def fetch_articles_from_given_date(date: date) -> list[dict]:
    """
    Fetch articles from the RSS feed published on the given date.

    Args:
        date (date): The publication date to filter articles by.

    Returns:
        list[dict]: A list of articles published on the given date.
    """
    feed = feedparser.parse(RSS_URL)
    recent = []
    for entry in feed.entries:
        published_date = get_entry_published_date(entry)
        if published_date != date:
            continue

        recent.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.get("summary", ""),
        })
    return recent


def build_txt(articles: list[dict], date: date) -> str:
    """
    Build a plain text digest from a list of articles.

    Args:
        articles (list[dict]): List of articles to include.
        date (date): The date of the digest.

    Returns:
        str: The full plain text content.
    """
    lines = [f"AI News Digest — {date.strftime('%B %d, %Y')}\n"]
    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. {article['title']}\n")
        lines.append(article["summary"])
        lines.append(f"\nRead more: {article['link']}\n")
        lines.append("-" * 40 + "\n")
    return "\n".join(lines)


def send_digest_to_discord(text_content: str, date: date) -> None:
    """
    Send the digest as a plain text file attachment to Discord via webhook.

    Args:
        text_content (str): The plain text content to send.
        date (date): The date of the digest.
    """
    filename = f"ai_digest_{date.strftime('%Y-%m-%d')}.txt"
    file_obj = io.BytesIO(text_content.encode("utf-8"))

    response = requests.post(
        WEBHOOK_URL,
        data={
            "payload_json": json.dumps({
                "content": (
                    f"Your AI News Digest for {date.strftime('%B %d, %Y')}"
                    " is ready!"
                )
            })
        },
        files={
            "file": (filename, file_obj, "text/plain")
        }
    )
    response.raise_for_status()


if __name__ == "__main__":
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    recent_articles = fetch_articles_from_given_date(yesterday)
    if not recent_articles:
        requests.post(
            WEBHOOK_URL, 
            json={"content": f"No new AI articles were published yesterday."}
        )
    else:
        text_content = build_txt(recent_articles, yesterday)
        send_digest_to_discord(text_content, yesterday)