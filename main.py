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


def send_msg_to_discord(msg: str) -> None:
    """
    Send a message to Discord.

    Args:
        msg (str): The message to send to Discord.

    Returns:
        None
    """
    response = requests.post(WEBHOOK_URL, json={"content": msg})
    response.raise_for_status()


if __name__ == "__main__":
    recent_articles = fetch_recent_articles()
    today = datetime.today().strftime("%B %d, %Y")
    msg = f"**{today}**"
    for i, article in enumerate(recent_articles):
        msg += f"**{article['title']}**\n" + \
            f"{article['summary']}\n" + \
            f"<{article['link']}>\n\n"
    send_msg_to_discord(msg)