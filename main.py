import requests  # Library for making HTTP requests
from bs4 import BeautifulSoup  # Library for parsing HTML and XML documents
import time  # Library for time-related tasks, like pausing execution
import smtplib # Library for sending emails (optional, for notifications)
from email.mime.text import MIMEText # For formatting email messages (optional)

# --- Configuration ---

# List of news website URLs to monitor
# IMPORTANT: Check the website's robots.txt and terms of service before scraping!
# Example websites (replace with your targets):
NEWS_WEBSITES = {
    "Example News Site 1": "https://www.example-news-site1.com/section",
    "Example News Site 2": "https://www.example-news-site2.com/politics",
    # Add more sites as needed
}

# List of keywords or topics to track
KEYWORDS = ["isdera", "isdera motors", "isderaAG"]

# --- Optional: Email Notification Settings ---
SEND_EMAIL_NOTIFICATIONS = False # Set to True to enable email notifications
SMTP_SERVER = "smtp.gmail.com"  # Your SMTP server (e.g., smtp.gmail.com)
SMTP_PORT = 587  # Common port for TLS
EMAIL_ADDRESS = "iskjfu@gmail.com" # Your email address
EMAIL_PASSWORD = "your_password" # Your email password (use app password if using Gmail)
RECIPIENT_EMAIL = "iskjfu@gmail.com" # Email address to send notifications to

# --- Helper Functions ---

def fetch_html(url):
    """Fetches HTML content from a given URL."""
    try:
        # Send an HTTP GET request to the URL
        # Include a User-Agent header to mimic a browser visit
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers, timeout=10) # Added timeout
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_news(html_content, base_url):
    """Parses HTML to find news headlines and links."""
    found_articles = {} # Dictionary to store {headline: link}
    if not html_content:
        return found_articles

    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # --- IMPORTANT: Customize this part for each website ---
        # Find HTML elements containing headlines and links.
        # This requires inspecting the website's HTML structure (using browser developer tools).
        # The example below assumes headlines are in <h2> tags with class 'headline'
        # and links are within <a> tags inside those <h2> tags.
        # You WILL need to adjust the selectors (e.g., 'h2', {'class': 'headline'}) for each target site.

        headlines = soup.find_all('h2', {'class': 'headline'}) # Example selector

        for headline_tag in headlines:
            headline_text = headline_tag.get_text(strip=True)
            link_tag = headline_tag.find('a') # Find the link within the headline tag

            if headline_text and link_tag and link_tag.has_attr('href'):
                link_href = link_tag['href']
                # Handle relative URLs (e.g., /article/story) by joining with the base URL
                if link_href.startswith('/'):
                    link_href = requests.compat.urljoin(base_url, link_href)
                found_articles[headline_text] = link_href
        # --- End of customization section ---

    except Exception as e:
        print(f"Error parsing HTML: {e}")

    return found_articles

def check_keywords(articles, keywords):
    """Checks if article headlines contain any of the specified keywords."""
    relevant_articles = {}
    for headline, link in articles.items():
        # Check if any keyword (case-insensitive) is in the headline
        if any(keyword.lower() in headline.lower() for keyword in keywords):
            relevant_articles[headline] = link
    return relevant_articles

def send_email(subject, body):
    """Sends an email notification (if enabled)."""
    if not SEND_EMAIL_NOTIFICATIONS:
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        print("Notification email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        print("Email login failed. Check credentials or app password settings.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- Main Monitoring Loop ---

if __name__ == "__main__":
    print("Starting news monitor...")
    # Keep track of previously found articles to avoid duplicates (optional)
    previously_found = set()

    try:
        while True: # Loop indefinitely (or change for a fixed number of runs)
            print(f"\n--- Checking for news at {time.ctime()} ---")
            all_relevant_articles_this_run = {}

            for site_name, url in NEWS_WEBSITES.items():
                print(f"Checking {site_name} ({url})...")
                html = fetch_html(url)
                if html:
                    articles = parse_news(html, url)
                    relevant_articles = check_keywords(articles, KEYWORDS)

                    # Filter out already seen articles
                    newly_found = {}
                    for headline, link in relevant_articles.items():
                        # Create a unique identifier for the article (e.g., link)
                        article_id = link
                        if article_id not in previously_found:
                            newly_found[headline] = link
                            previously_found.add(article_id) # Add to seen set

                    if newly_found:
                        print(f"Found {len(newly_found)} new relevant article(s) on {site_name}:")
                        for headline, link in newly_found.items():
                            print(f"  - {headline}: {link}")
                        all_relevant_articles_this_run.update(newly_found)
                    else:
                        print(f"No new relevant articles found on {site_name}.")
                time.sleep(2) # Be polite, wait a bit between requests to different sites

            # --- Notification ---
            if all_relevant_articles_this_run:
                email_subject = "News Monitor Alert: New Relevant Articles Found!"
                email_body = "Found the following new articles matching your keywords:\n\n"
                for headline, link in all_relevant_articles_this_run.items():
                    email_body += f"- {headline}\n  Link: {link}\n\n"
                send_email(email_subject, email_body)

            # --- Wait before next check ---
            check_interval_seconds = 3600 # Check every hour (3600 seconds)
            print(f"\nWaiting for {check_interval_seconds // 60} minutes before next check...")
            time.sleep(check_interval_seconds)

    except KeyboardInterrupt:
        print("\nStopping news monitor.")
