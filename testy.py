import os
import requests
import json
import random
from datetime import datetime
from urllib.parse import urlparse

print("🛡 SAFE MODE: Bot will not post to X")
print("🚀 Starting Firecrawl + SerpAPI SMART-AUTO debug run...")

firecrawl_api_key = os.getenv("FIRECRAWL_KEY")
serpapi_key = os.getenv("SERPAPI_KEY")

print("FIRECRAWL_KEY loaded:", bool(firecrawl_api_key))
print("SERPAPI_KEY loaded:", bool(serpapi_key))

if not firecrawl_api_key or not serpapi_key:
    print("❌ ERROR: Missing FIRECRAWL_KEY or SERPAPI_KEY. Check GitHub Secrets.")
    exit(1)

HISTORY_FILE = "tweet_history.json"
TRUSTED_FILE = "trusted_domains.json"
BLACKLIST_FILE = "blacklist.json"  # New blacklist file
DAILY_TWEET_CAP = 6  # Limit to 3 tweets per run
MAX_URLS_PER_QUERY = 10  # Process up to 5 URLs per query

SEARCH_QUERIES = [
    "Agentic AI",
    "free AI courses",
    "AI prompting tips",
    "AI tutorials",
    "free AI certificates"
]

BASE_TRUSTED = [
    "medium.com",
    "udemy.com",
    "deeplearning.ai",
    "classcentral.com",
    "edx.org",
    "coursera.org",
    "towardsdatascience.com",
    "ai.googleblog.com",
    "openai.com",
    "arxiv.org"
]

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def load_history():
    return load_json(HISTORY_FILE, [])

def save_history(history):
    save_json(HISTORY_FILE, history)

def load_trusted():
    learned = load_json(TRUSTED_FILE, [])
    return list(set(BASE_TRUSTED + learned))

def save_trusted(domains):
    learned = [d for d in domains if d not in BASE_TRUSTED]
    save_json(TRUSTED_FILE, learned)

def load_blacklist():
    return load_json(BLACKLIST_FILE, [])

def save_blacklist(domains):
    save_json(BLACKLIST_FILE, domains)

def crawl_url(single_url):
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
    except requests.exceptions.RequestException as e:
        print(f"❌ Crawl error for {single_url}: {e}")
        return {"status_code": r.status_code if 'r' in locals() else 0}  # Return status for checking

def scrape_url(single_url):
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
    except requests.exceptions.RequestException as e:
        print(f"❌ Scrape error for {single_url}: {e}")
        return {"status_code": r.status_code if 'r' in locals() else 0}

def scrape_url(single_url):
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

def extract_domain(url):
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""

def get_serpapi_results(query, trusted_domains, blacklist):
    api_url = f"https://serpapi.com/search.json?q={query}&api_key={serpapi_key}&num={MAX_URLS_PER_QUERY}"
    urls = []
    new_domains = set()
    try:
        r = requests.get(api_url)
        r.raise_for_status()
        data = r.json()
        for res in data.get("organic_results", []):
            link = res.get("link")
            if not link:
                continue
            domain = extract_domain(link)
            if (domain in trusted_domains and 
                "reddit.com" not in domain and 
                "youtube.com" not in domain and 
                domain not in blacklist):
                urls.append(link)
                if domain not in trusted_domains:
                    new_domains.add(domain)
    except Exception as e:
        print(f"❌ SerpAPI error for {query}: {e}")
    return urls, new_domains

def main():
    history = load_history()
    trusted_domains = load_trusted()
    blacklist = load_blacklist()
    all_urls = []
    newly_trusted = set()
    tweet_count = 0

    print(f"📋 Initial trusted domains: {trusted_domains}")
    print(f"📋 Initial blacklist: {blacklist}")

    for q in SEARCH_QUERIES:
        print(f"🔎 Searching via SerpAPI: {q}")
        urls, new_domains = get_serpapi_results(q, trusted_domains, blacklist)
        print(f"   Found {len(urls)} links ({len(new_domains)} new domains)")
        all_urls.extend(urls)
        newly_trusted.update(new_domains)

    print(f"🌐 Total unique URLs to process: {len(all_urls)}")

    # Apply cap to new domains
    if newly_trusted:
        limited_new = sorted(list(newly_trusted))[:DAILY_NEW_DOMAIN_CAP]
        print(f"🧠 Learning {len(limited_new)} new domains today: {limited_new}")
        trusted_domains.extend(limited_new)
        trusted_domains = sorted(set(trusted_domains))
        save_trusted(trusted_domains)

    all_urls = list(set(all_urls))[:MAX_URLS_PER_QUERY * len(SEARCH_QUERIES)]  # Cap total URLs

    for source in all_urls:
        if tweet_count >= DAILY_TWEET_CAP:
            print(f"⏹ Reached daily tweet cap of {DAILY_TWEET_CAP}")
            break

        if source in history:
            print(f"⏭ Skipping duplicate from history: {source}")
            continue

        domain = extract_domain(source)
        data = crawl_url(source)
        if not data or "data" not in data or not data["data"]:
            print(f"⚠ No crawl data for {source}, falling back to scrape...")
            data = scrape_url(source)

        if "data" not in data:
            print(f"⚠ No usable data for {source}, checking markdown fallback...")
            markdown = data.get("markdown", "")
            if markdown:
                entries = [{"title": "Scraped Content", "url": source, "content": markdown}]
            else:
                # Check for 429 status in crawl or scrape response
                crawl_status = crawl_url(source).get("status_code", 0)
                scrape_status = scrape_url(source).get("status_code", 0)
                if crawl_status == 429 or scrape_status == 429:
                    print(f"🚫 Adding {domain} to blacklist due to 429 errors")
                    if domain not in blacklist:
                        blacklist.append(domain)
                        save_blacklist(blacklist)
                continue

        # Handle data["data"] type
        if isinstance(data["data"], list):
            entries = data["data"]
        elif isinstance(data["data"], dict):
            entries = [data["data"]]
        elif isinstance(data["data"], str):
            entries = [{"title": "Scraped Content", "url": source, "content": data["data"]}]
        else:
            print(f"⚠ Unexpected data type for {source}: {type(data['data'])}")
            continue

        # Process each entry
        for entry in entries:
            if isinstance(entry, dict):
                page_title = entry.get("title", "Untitled")
                page_url = entry.get("url", source)
            else:
                page_title = "Scraped Content"
                page_url = source
            if not page_url:
                continue

            tweet_text = make_tweet(page_title, page_url)
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            print(f"📝 WOULD TWEET: {tweet_text}")
            history.append(page_url)
            save_history(history)
            tweet_count += 1
            if tweet_count >= DAILY_TWEET_CAP:
                break

    print(f"[{datetime.now()}] ✅ Smart auto-updating safe mode run complete. No tweets sent.")

if __name__ == "__main__":
    main()
