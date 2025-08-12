import os
import requests
import json
import random
from datetime import datetime

print("🛡 SAFE MODE: Bot will not post to X")
print("🚀 Starting Firecrawl AUTO-UPDATING debug run...")

firecrawl_api_key = os.getenv("FIRECRAWL_KEY")
print("FIRECRAWL_KEY loaded:", firecrawl_api_key is not None)

if not firecrawl_api_key:
    print("❌ ERROR: FIRECRAWL_KEY is missing. Check your GitHub Secrets.")
    exit(1)

HISTORY_FILE = "tweet_history.json"

SEARCH_QUERIES = [
    "Agentic AI",
    "Free AI courses",
    "AI Prompting tips",
    "AI tutorials",
    "free AI certificates",
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def scrape_url(single_url):
    """Scrape one page via Firecrawl /v1/scrape."""
    api_url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }
    payload = {"url": single_url, "formats": ["markdown"]}

    try:
        r = requests.post(api_url, json=payload, headers=headers)
        print(f"🔍 Scraping {single_url} → status: {r.status_code}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Scrape error for {single_url}: {e}")
        return {}

def crawl_url(single_url):
    """Crawl one page via Firecrawl /v1/crawl."""
    api_url = "https://api.firecrawl.dev/v1/crawl"
    headers = {
        "Authorization": f"Bearer {firecrawl_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": single_url,
        "maxDepth": 1,
        "maxDiscoveryDepth": 1,
        "crawlEntireDomain": False,
        "allowExternalLinks": False,
        "allowSubdomains": False,
        "scrapeOptions": {
            "onlyMainContent": True,
            "removeBase64Images": True,
            "blockAds": True,
            "formats": ["markdown"]
        }
    }

    try:
        r = requests.post(api_url, json=payload, headers=headers)
        print(f"🔍 Crawling {single_url} → status: {r.status_code}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Crawl error for {single_url}: {e}")
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

def get_search_results(query):
    """Scrape Google search results page for a query."""
    google_search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    results = scrape_url(google_search_url)
    urls = []
    if "data" in results:
        for entry in results["data"]:
            if "url" in entry and entry["url"].startswith("http"):
                urls.append(entry["url"])
    return urls

def main():
    history = load_history()
    all_urls = []

    # Step 1: Get fresh URLs from Google searches
    for q in SEARCH_QUERIES:
        print(f"🔎 Searching for: {q}")
        urls = get_search_results(q)
        print(f"   Found {len(urls)} candidate links")
        all_urls.extend(urls)

    # Deduplicate URLs
    all_urls = list(set(all_urls))

    # Step 2: Crawl or scrape each URL
    for source in all_urls:
        if source in history:
            print(f"⏭ Skipping duplicate from history: {source}")
            continue

        data = crawl_url(source)

        if not data or "data" not in data or not data["data"]:
            print(f"⚠ No crawl data for {source}, falling back to scrape...")
            data = scrape_url(source)

        if "data" not in data:
            print(f"⚠ No usable data for {source}")
            continue

        for entry in data["data"]:
            page_title = entry.get("title", "Untitled")
            page_url = entry.get("url", source)
            if not page_url:
                continue

            tweet_text = make_tweet(page_title, page_url)
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            print(f"📝 WOULD TWEET: {tweet_text}")
            history.append(page_url)
            save_history(history)

    print(f"[{datetime.now()}] ✅ Auto-updating safe mode run complete. No tweets sent.")

if __name__ == "__main__":
    main()
