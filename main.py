import os
import requests
import time
import random
import json
from datetime import datetime

print("Firecrawl key loaded:", os.getenv("FIRECRAWL_KEY") is not None)
print("X token loaded:", os.getenv("X_BEARER_TOKEN") is not None)

# Load API keys from environment variables
firecrawl_api_key = os.getenv("FIRECRAWL_KEY")
bearer_token = os.getenv("X_BEARER_TOKEN")

# File to store tweet history
HISTORY_FILE = "tweet_history.json"

# Chance to skip posting for the day (simulating human off days)
OFF_DAY_CHANCE = 0.15  # 15% of days no tweets

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def get_links(query):
    url = "https://api.firecrawl.com/v1/scrape"
    payload = {"query": query, "maxResults": 5}
    headers = {"Authorization": f"Bearer {firecrawl_api_key}"}
    r = requests.post(url, json=payload, headers=headers)
    results = r.json().get("data", [])
    return [{"title": r["title"], "url": r["url"]} for r in results]

def post_tweet(text):
    url = "https://api.x.com/2/tweets"
    headers = {"Authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"}
    payload = {"text": text}
    r = requests.post(url, json=payload, headers=headers)
    print(f"[{datetime.now()}] {r.status_code} - {text}")
    return r.status_code == 201

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
    if random.random() < OFF_DAY_CHANCE:
        print(f"[{datetime.now()}] Off day — no tweets today.")
        return

    queries = [
        "Agentic AI site:medium.com OR site:huggingface.co",
        "free AI courses site:deeplearning.ai OR site:coursera.org"
    ]

    history = load_history()

    for query in queries:
        for result in get_links(query):
            if result['url'] in history:
                continue

            tweet_text = make_tweet(result['title'], result['url'])
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            delay = random.randint(60 * 60 * 4, 60 * 60 * 8)  # Wait 4–8 hours
            print(f"Waiting {delay // 3600}h before posting: {tweet_text}")
            time.sleep(delay)

            if post_tweet(tweet_text):
                history.append(result['url'])
                save_history(history)

if __name__ == "__main__":
    main()

