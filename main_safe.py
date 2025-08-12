import os
import requests
import json
import random
from datetime import datetime

print("🛡 SAFE MODE: Bot will not post to X")
print("🚀 Starting Firecrawl CRAWL debug run...")

# Load API key
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

def crawl_urls(urls):
    """Crawl multiple URLs using Firecrawl /v1/crawl API."""
    url = "https://api.firecrawl.dev/v1/crawl"
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "urls": urls,  # Crawls each URL provided
        "maxDepth": 2,
        "maxDiscoveryDepth": 2,
        "crawlEntireDomain": False,
        "allowExternalLinks": False,
        "allowSubdomains": False,
        "scrapeOptions": {
            "onlyMainContent": True,
            "removeBase64Images": True,
            "blockAds": True,
            "formats": ["markdown,html,screenshot"],
            "location": {
                "country": "US",
                "languages": ["en-US"]
            }
        }
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        print(f"🔍 Firecrawl status: {r.status_code}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ ERROR in crawl_urls: {e}")
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

    # URLs to crawl (can add more trusted sources)
    urls = [
        "https://medium.com/tag/agentic-ai",
        "https://huggingface.co/blog",
        "https://deeplearning.ai/resources/",
        "https://www.classcentral.com/subject/ai",
    ]

    print("🌐 Crawling URLs:", urls)
    crawl_data = crawl_urls(urls)

    # The response structure may vary — adjust parsing based on actual Firecrawl output
    if "data" not in crawl_data:
        print("⚠ No 'data' key in Firecrawl response.")
        print("Raw response:", json.dumps(crawl_data, indent=2)[:1000], "...")
        return

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
