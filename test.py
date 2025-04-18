import feedparser
import time # For accessing published_parsed time tuple

# --- Configuration ---
# Replace with the actual RSS feed URL you want to monitor
# Example using MotorTrend's main feed:
FEED_URL = "https://www.motortrend.com/feed/"
# You can often find feed URLs by looking for an RSS icon on the website
# or searching "[website name] RSS feed".

# --- Fetch and Parse the Feed ---

print(f"Fetching and parsing feed from: {FEED_URL}")
# The parse() function downloads and parses the feed content.
feed = feedparser.parse(FEED_URL)
print(feed)
# --- Check for Errors ---
# feedparser sets feed.bozo to 1 if potential problems were encountered during parsing
if feed.bozo:
    print(f"Warning: Potential feed parsing issue detected. Bozo flag is set.")
    # You might want to inspect the bozo_exception for details
    if hasattr(feed, 'bozo_exception'):
        print(f"Bozo Exception: {feed.bozo_exception}")

# --- Access Feed Metadata ---
# Access information about the feed itself (the 'channel')
if 'title' in feed.feed:
    print(f"\nFeed Title: {feed.feed.title}")
if 'link' in feed.feed:
    print(f"Feed Link: {feed.feed.link}")
if 'description' in feed.feed:
    print(f"Feed Description: {feed.feed.description}")
print("-" * 20)

# --- Access Feed Entries (Items) ---
# feed.entries is a list of dictionaries, each representing an item/article
if not feed.entries:
    print("No entries found in the feed.")
else:
    print(f"Found {len(feed.entries)} entries:\n")
    # Loop through the first 5 entries (or all if fewer than 5)
    for entry in feed.entries[:5]:
        title = entry.get('title', 'N/A') # Use .get() for safe access
        link = entry.get('link', 'N/A')
        summary = entry.get('summary', 'N/A') # Or 'description'

        # feedparser automatically parses dates into a time.struct_time tuple
        published_time = entry.get('published_parsed', None)
        published_str = "N/A"
        if published_time:
            # Format the time tuple into a readable string
            try:
                published_str = time.strftime('%Y-%m-%d %H:%M:%S', published_time)
            except Exception:
                published_str = "Invalid Date Format" # Handle potential errors

        print(f"Title: {title}")
        print(f"Link: {link}")
        print(f"Published: {published_str}")
        # The summary can be long and might contain HTML, print carefully
        # print(f"Summary: {summary[:200]}...") # Print first 200 chars
        print("-" * 10)