import os
import requests
import json
import random
from datetime import datetime

print("🛡 SAFE MODE: Bot will not post to X")
print("🚀 Starting Firecrawl-only debug run...")

# Check if secrets exist
firecrawl_api_key = os.getenv("FIRECRAWL_KEY")
bearer_token = os.getenv("X_BEARER_TOKEN")  # Not used in safe mode
print("FIRECRAWL_KEY loaded:", firecrawl_api_key is not None)
print("X_BEARER_TOKEN loaded:", bearer_token is not None)

if not firecrawl_api_key:
    print("❌ ERROR: FIRECRAWL_KEY is missing. Check your GitHub Secrets.")
    exit(1)

HISTORY_FILE = "tweet_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def get_links(query):
    url = "https://api.firecrawl.dev/v1/scrape"
    payload = {"query": query, "maxResults": 5}
    headers = {"Authorization": f"Bearer {firecrawl_api_key}"}
    try:
        r = requests.post(url, json=payload, headers=headers)
        print(f"🔍 Firecrawl status: {r.status_code}")
        print("📄 Firecrawl raw response:", r.text[:500], "...")
        r.raise_for_status()
        results = r.json().get("data", [])
        return [{"title": r["title"], "url": r["url"]} for r in results]
    except Exception as e:
        print(f"❌ ERROR in get_links: {e}")
        return []

def make_tweet(title, url):
    prefixes = ["🚀", "📢", "🔥", "💡", "🎯", "🧠"]
    templates = [
        "{prefix} {title} {url}",
        "{prefix} Check this out: {title} {url}",
        "{prefix} New resource: {title} {url}",
        "{prefix} Just found: {title} {url}",
        "{prefix} Insight drop: {title} {url}"
    ]
    template = random.choice(templates)
    return template.format(prefix=random.choice(prefixes), title=title, url=url)

def main():
    queries = [
        "Agentic AI tutorials", 
        "free AI courses site:https://www.coursera.org",
        "site:https://www.coursera.org"
    ]

    history = load_history()

    for query in queries:
        print(f"🔎 Searching Firecrawl for: {query}")
        for result in get_links(query):
            if result['url'] in history:
                print(f"⏭ Skipping duplicate: {result['url']}")
                continue

            tweet_text = make_tweet(result['title'], result['url'])
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            
            print(f"📝 WOULD TWEET: {tweet_text}")
            history.append(result['url'])
            save_history(history)

    print(f"[{datetime.now()}] ✅ Safe mode run complete. No tweets sent.")

if __name__ == "__main__":
    main()
