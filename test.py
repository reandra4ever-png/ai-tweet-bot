import os
import time

print("🚀 Test script started")

# Check if secrets exist
print("FIRECRAWL_KEY loaded:", os.getenv("FIRECRAWL_KEY") is not None)
print("X_BEARER_TOKEN loaded:", os.getenv("X_BEARER_TOKEN") is not None)

# Simulate doing some work
for i in range(5):
    print(f"⏳ Still running... step {i+1}/5")
    time.sleep(60)  # wait 1 minute

print("✅ Test script finished successfully!")
