import os
import requests
import json
import random
from datetime import datetime

print("🛡 SAFE MODE: Bot will not post to X")
print("🚀 Starting Firecrawl CRAWL debug run...")

firecrawl_api_key = os.getenv("FIRECRAWL_KEY")
print("FIRECRAWL_KEY loaded:", firecrawl_api_key is not None)

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

def crawl_url(single_url):
    """Crawl one URL using Firecrawl /v1/crawl API."""
    api_url = "https://api.firecrawl.dev/v1/crawl"
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "url": single_url,
        "maxDepth": 2,
        "maxDiscoveryDepth": 2,
        "crawlEntireDomain": False,
        "allowExternalLinks": False,
        "allowSubdomains": False,
        "scrapeOptions": {
            "onlyMainContent": True,
            "removeBase64Images": True,
            "blockAds": True,
            "formats": ["markdown"],
            "location": {
                "country": "US",
                "languages": ["en-US"]
            }
        }
    }

    try:
        r = requests.post(api_url, json=payload, headers=headers)
        print(f"🔍 Crawling {single_url} → status: {r.status_code}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ ERROR in crawl_url for {single_url}: {e}")
        return {}

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
    return template.format(prefix=random.choice(prefixes), title=title.strip(), url=url)

def main():
    history = load_history()

    urls = [
        "https://medium.com/tag/agentic-ai",
        "https://huggingface.co/blog",
        "https://deeplearning.ai/resources/",
        "https://www.classcentral.com/subject/ai",
    ]

    for source in urls:
        crawl_data = crawl_url(source)

        if "data" not in crawl_data:
            print(f"⚠ No 'data' key in Firecrawl response for {source}.")
            print("Raw response:", json.dumps(crawl_data, indent=2)[:500], "...")
            continue

        for entry in crawl_data["data"]:
            page_title = entry.get("title", "Untitled")
            page_url = entry.get("url")
            if not page_url:
                continue

            if page_url in history:
                print(f"⏭ Skipping duplicate: {page_url}")
                continue

            tweet_text = make_tweet(page_title, page_url)
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            print(f"📝 WOULD TWEET: {tweet_text}")
            history.append(page_url)
            save_history(history)

    print(f"[{datetime.now()}] ✅ Safe mode crawl complete. No tweets sent.")

if __name__ == "__main__":
    main()
