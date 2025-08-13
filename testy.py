import os
import json
import random
from datetime import datetime
from urllib.parse import urlparse
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import Spider
from scrapy.http import Request

print("🛡 SAFE MODE: Bot will not post to X")
print("🚀 Starting Scrapy + SerpAPI SMART-AUTO debug run...")

serpapi_key = os.getenv("SERPAPI_KEY")

print("SERPAPI_KEY loaded:", bool(serpapi_key))

if not serpapi_key:
    print("❌ ERROR: Missing SERPAPI_KEY. Check GitHub Secrets.")
    exit(1)

HISTORY_FILE = "tweet_history.json"
TRUSTED_FILE = "trusted_domains.json"
BLACKLIST_FILE = "blacklist.json"
DAILY_TWEET_CAP = 3
MAX_URLS_PER_QUERY = 5

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

class SimpleSpider(Spider):
    name = "simple"
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 30,  # 30-second timeout
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self, url=None, *args, **kwargs):
        super(SimpleSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []

    def parse(self, response):
        yield {
            "title": response.css("title::text").get(default="Untitled").strip(),
            "url": response.url,
            "content": response.text[:1000]  # Limit content for brevity
        }

def scrape_url(single_url):
    process = CrawlerProcess(settings={
        "LOG_ENABLED": False,
        "DOWNLOAD_DELAY": 2  # Avoid overloading sites
    })
    deferred = process.crawl(SimpleSpider, url=single_url)
    process.start()
    results = [item for item in deferred.result]
    return {"data": results[0]} if results else {}

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

    if newly_trusted:
        limited_new = sorted(list(newly_trusted))[:DAILY_NEW_DOMAIN_CAP]
        print(f"🧠 Learning {len(limited_new)} new domains today: {limited_new}")
        trusted_domains.extend(limited_new)
        trusted_domains = sorted(set(trusted_domains))
        save_trusted(trusted_domains)

    all_urls = list(set(all_urls))[:MAX_URLS_PER_QUERY * len(SEARCH_QUERIES)]

    for source in all_urls:
        if tweet_count >= DAILY_TWEET_CAP:
            print(f"⏹ Reached daily tweet cap of {DAILY_TWEET_CAP}")
            break

        if source in history:
            print(f"⏭ Skipping duplicate from history: {source}")
            continue

        domain = extract_domain(source)
        data = scrape_url(source)

        if not data or "data" not in data or not data["data"]:
            print(f"⚠ No scrape data for {source}, skipping...")
            if any("429" in str(e) for e in [scrape_url(source)]):  # Simplified 429 check
                print(f"🚫 Adding {domain} to blacklist due to 429 errors")
                if domain not in blacklist:
                    blacklist.append(domain)
                    save_blacklist(blacklist)
            continue

        entries = data["data"] if isinstance(data["data"], list) else [data["data"]]

        for entry in entries:
            if isinstance(entry, dict):
                page_title = entry.get("title", "Untitled")
                page_url = entry.get("url", source)
            else:
                page_title = "Scraped Content"
                page_url = source
            if not page_url:
                continue

            tweet_text = f"{random.choice(['🚀', '📢', '🔥', '💡', '🎯', '🧠'])} {page_title} {page_url}"
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
