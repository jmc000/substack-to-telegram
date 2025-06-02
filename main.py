import feedparser
import requests
import os
from dotenv import load_dotenv

load_dotenv()

FEED_URL = "https://jmc0.substack.com/feed"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "last_post.txt"

def load_last_post():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_last_post(post_id):
    with open(STATE_FILE, "w") as f:
        f.write(post_id)

def send_to_telegram(title, link, summary, image_url=None):
    message = f"📜 <b>Nouvelle publication Substack</b>\n\n┌────────────\n<b>{title}</b>\n<i>{summary}</i>\n└───────────────\n\n➤ <a href=\"{link}\">Lien</a>\n"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    response = requests.post(url, data=payload)
    if not response.ok:
        print("Failed to send message:", response.text)
    else:
        print("Message sent.")

def main():
    print("-> 1")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    print("-> 2")
    response = requests.get(FEED_URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch feed: HTTP {response.status_code}")
        return

    print("-> 3")
    feed = feedparser.parse(response.content)
    print("-> 4")

    if feed.bozo:
        print("Failed to parse feed:", feed.bozo_exception)
        return

    if not feed.entries:
        print("No entries found.")
        return

    latest = feed.entries[0]
    latest_id = latest.get("id") or latest.get("link")
    last_sent = load_last_post()

    if latest_id != last_sent:
        print("New post found, sending to Telegram.")
        summary = latest.get("summary") or latest.get("description") or ""
        summary = summary[:500]
        image_url = None
        if "media_content" in latest and latest.media_content:
            image_url = latest.media_content[0].get("url")
        elif "links" in latest:
            for link in latest.links:
                if link.get("rel") == "enclosure" and link.get("type", "").startswith("image/"):
                    image_url = link.get("href")
                    break

        send_to_telegram(latest.title, latest.link, summary, image_url)
        save_last_post(latest_id)
    else:
        print("No new post.")

if __name__ == "__main__":
    main()

