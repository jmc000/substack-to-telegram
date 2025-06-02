from dotenv import load_dotenv
import feedparser
import requests
import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

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
    message = f"📝 <b>{title}</b>\n\n{summary}\n\n<a href=\"{link}\">Read more</a>"
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

    # Optional: send image if available
    if image_url:
        photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        photo_payload = {
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": title
        }
        photo_resp = requests.post(photo_url, data=photo_payload)
        if not photo_resp.ok:
            print("Failed to send photo:", photo_resp.text)
        else:
            print("Photo sent.")

def main():
    feed = feedparser.parse(FEED_URL)

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

        # Try to get summary or description text
        summary = latest.get("summary") or latest.get("description") or ""
        summary = summary[:500]

        # Try to get the image URL from media_content or enclosure
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

