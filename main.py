import requests  # Library for making HTTP requests
from bs4 import BeautifulSoup  # Library for parsing HTML and XML documents
import time  # Library for time-related tasks, like pausing execution
import smtplib # Library for sending emails (optional, for notifications)
from email.mime.text import MIMEText # For formatting email messages (optional)
from dotenv import load_dotenv
import os
from urllib.parse import urljoin
import sys
import feedparser
import json
# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service # Or Firefox service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options # Or Firefox options
from selenium.common.exceptions import TimeoutException, WebDriverException
# --- Configuration ---
load_dotenv()

# Load NEWS_WEBSITES and KEYWORDS from config.json file
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        NEWS_WEBSITES = data['websites']
        KEYWORDS = data['keywords']
except FileNotFoundError:
    print('Error: The file config.json was not found')
except json.JSONDecodeError:
    print('Error: Invalid JSON found in config.json')
except Exception as e:
    print("Error: {e}")

# --- Optional: Email Notification Settings ---
SEND_EMAIL_NOTIFICATIONS = False # Set to True to enable email notifications
SMTP_SERVER = 'smtp.gmail.com'  # Your SMTP server (e.g., smtp.gmail.com)
SMTP_PORT = 587  # Common port for TLS
EMAIL_ADDRESS = os.getenv('EMAIL_USER') # Your email address
EMAIL_PASSWORD = os.getenv('EMAIL_PASS') # Your email password (use app password if using Gmail)
RECIPIENT_EMAIL = os.getenv('EMAIL_RECEPIENT') # Email address to send notifications to

# --- Helper Functions ---

def safe_print(text):
    """Prints text safely, replacing characters incompatible with the console."""
    try:
        encoded_text = text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(encoded_text)
    except Exception as e:
        print(f"Error printing message: {e}")
        print(repr(text))

def fetch_html_without_selenium(url):
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
     
def fetch_html_with_selenium(url, site_name, selenium_selector_str):
    """Fetches dynamically loaded HTML content from a given URL using Selenium."""
    driver = None # Initialize driver to None
    html_content = None # Initialize html_content
    # Define a filename for saving the source code
    source_filename = f"{site_name}_source.html"
    try:
        # Setup Chrome options (headless recommended for background execution)
        chrome_options = Options()
        chrome_options.add_argument("--headless") # Run without opening a browser window
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36") # Set user agent

        # Initialize WebDriver (assuming chromedriver is in PATH)
        # If not in PATH, use: driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5) # Basic implicit wait

        safe_print(f"Loading URL with Selenium: {url}")
        driver.get(url)

        wait_timeout = 25 # Increased timeout slightly
        wait_selector_str = selenium_selector_str # Wait for any link inside the likely container
        wait_selector = (By.CSS_SELECTOR, wait_selector_str)

        safe_print(f"Waiting up to {wait_timeout}s for element '{wait_selector_str}' to load...")
        WebDriverWait(driver, wait_timeout).until(
            EC.presence_of_element_located(wait_selector)
            # Alternative: Wait for visibility if presence isn't enough
            # EC.visibility_of_element_located(wait_selector)
        )
        safe_print("Element found, page likely loaded.")

        # Optional: Add a small extra sleep just in case more JS needs to run
        time.sleep(5)

        # Get the page source *after* JavaScript has potentially run
        html_content = driver.page_source
        safe_print(f"Successfully fetched HTML for {url}")

        # --- Save the fetched HTML for debugging ---
        try:
            with open(source_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            safe_print(f"Saved fetched HTML source to '{source_filename}'")
        except Exception as save_e:
            safe_print(f"Could not save HTML source to file: {save_e}")
        # --- End Save HTML ---

        return html_content

    except TimeoutException:
        safe_print(f"Error: Timed out waiting for element '{wait_selector_str}' on {url}. Page might not have loaded correctly or selector is wrong.")
        # Try to get and save page source even on timeout for debugging
        if driver:
             try:
                 html_content = driver.page_source
                 with open(source_filename, "w", encoding="utf-8") as f:
                     f.write(html_content if html_content else "")
                 safe_print(f"Saved HTML source (on timeout) to '{source_filename}' - PLEASE INSPECT THIS FILE.")
                 return html_content # Return potentially incomplete HTML
             except Exception as save_e:
                 safe_print(f"Could not save HTML source to file after timeout: {save_e}")
        return None # Indicate failure
    except WebDriverException as e:
        safe_print(f"Error during Selenium fetch for {url}: {e}")
        return None
    except Exception as e:
        safe_print(f"An unexpected error occurred during Selenium fetch for {url}: {e}")
        return None
    finally:
        # Ensure the browser is closed even if errors occur
        if driver:
            safe_print("Closing Selenium browser.")
            driver.quit()


def parse_news(html_content, base_url,soup_ele,soup_identifier):
    """Parses HTML (potentially rendered by JS) to find news headlines and links."""
    found_articles = {}
    if not html_content:
        safe_print("parse_news received no HTML content.")
        return found_articles

    try:
        soup = BeautifulSoup(html_content, 'lxml')
        headline_tags = soup.find_all(soup_ele, soup_identifier) 

        safe_print(f"Found {len(headline_tags)} potential headline tags.")

        if not headline_tags:
             safe_print("Selector did not find any headline tags. Please check the selector and the saved HTML source.")

        # Assuming the selector finds the <a> tags directly:
        for link_tag in headline_tags:
             headline_text = link_tag.get_text(strip=True)

             if headline_text and link_tag.has_attr('href'):
                 link_href = link_tag['href']
                 # Handle relative URLs
                 if link_href.startswith('/'):
                     link_href = urljoin(base_url, link_href)

                 # Basic check for valid URL structure
                 if link_href.startswith(('http://', 'https://')):
                     # Avoid duplicates based on headline text for this run
                     if headline_text not in found_articles:
                        found_articles[headline_text] = [link_href,'']
                 else:
                     safe_print(f"Skipping invalid or relative link: {link_href}")

    except Exception as e:
        safe_print(f"Error parsing HTML for {base_url}: {e}")
        import traceback
        safe_print(traceback.format_exc())


    return found_articles

def parse_rss(FEED_URL):
    print(f"Fetching and parsing feed from: {FEED_URL}")
    # The parse() function downloads and parses the feed content.
    feed = feedparser.parse(FEED_URL)

    found_articles = {}
    # --- Check for Errors ---
    # feedparser sets feed.bozo to 1 if potential problems were encountered during parsing
    if feed.bozo:
        print(f"Warning: Potential feed parsing issue detected. Bozo flag is set.")
        # You might want to inspect the bozo_exception for details
        if hasattr(feed, 'bozo_exception'):
            print(f"Bozo Exception: {feed.bozo_exception}")

    # --- Access Feed Entries (Items) ---
    # feed.entries is a list of dictionaries, each representing an item/article
    if not feed.entries:
        print("No entries found in the feed.")
    else:
        print(f"Found {len(feed.entries)} entries:\n")
        # Loop through the first 5 entries (or all if fewer than 5)
        for entry in feed.entries[:5]:
            headline = entry.get('title', 'N/A') # Use .get() for safe access
            link = entry.get('link', 'N/A')
            description = entry.get('description', 'N/A')

            found_articles[headline] = [link,description]
    return found_articles

# (check_keywords and send_email functions remain the same)
def check_keywords(articles, keywords):
    """Checks if article headlines contain any of the specified keywords."""
    relevant_articles = {}
    for headline, item in articles.items():
        link = item[0]
        description = item[1]
        # Check if any keyword (case-insensitive) is in the headline
        matched_keywords = [keyword for keyword in keywords 
                    if keyword.lower() in headline.lower() or keyword.lower() in description.lower()]
        if matched_keywords:
           relevant_articles[headline] = [link,matched_keywords,description] 
    return relevant_articles

def send_email(subject, body):
    """Sends an email notification (if enabled)."""
    if not SEND_EMAIL_NOTIFICATIONS:
        return
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string().encode('utf-8'))
        safe_print("Notification email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        safe_print("Email login failed. Check credentials or app password settings.")
    except Exception as e:
        safe_print(f"Failed to send email: {e}")


# --- Main Monitoring Loop ---

if __name__ == "__main__":
    safe_print("Starting news monitor ...")
    previously_found = set() # Using links to track previously found articles

    try:
        while True:
            current_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            safe_print(f"\n--- Checking for news at {current_time_str} ---")
            all_relevant_articles_this_run = {}

            for website in NEWS_WEBSITES:
                safe_print(f"Checking {website['name']} ({website['url']})...")

                # Retrieve articles either using RSS or webscraping from HTML             
                if website['rss']:
                    articles = parse_rss(website['url'])
                else:
                    html = fetch_html_with_selenium(website['url'], website['name'],website['selenium_selector_str']) if website['selenium'] else fetch_html_without_selenium(website['url'])
                    articles = parse_news(html, website['url'],website['soup_selector_ele'],website['soup_selector_identifier'])
                # Search articles for any keywords
                if articles:   
                    relevant_articles = check_keywords(articles, KEYWORDS)
                    newly_found = {}
                    for headline, item in relevant_articles.items():
                        article_id = item[0] # Use link as the unique ID
                        if article_id not in previously_found:
                            newly_found[headline] = [item[0],item[1],item[2]]
                            previously_found.add(article_id) # Add link to seen set

                    if newly_found:
                        safe_print(f"Found {len(newly_found)} new relevant article(s) on {website['name']}:")
                        for headline, item in newly_found.items():
                            safe_print(f"  - Headline: {headline}")
                            safe_print(f"    Link: {item[0]}")
                            safe_print(f"    Matched Keywords: {item[1]}")
                            safe_print(f"    Description: {item[2]}")
                        all_relevant_articles_this_run.update(newly_found)
                    else:
                        safe_print(f"No new relevant articles found on {website['name']}.")
                else:
                    safe_print(f"Failed to fetch HTML for {website['name']}.")

                # Add a delay between checking different sites
                safe_print(f"Waiting a few seconds before checking next site...")
                time.sleep(5) # Increased sleep time as Selenium is more resource-intensive

            # --- Notification ---
            if all_relevant_articles_this_run:
                email_subject = "News Monitor Alert: New Relevant Articles Found!"
                email_body = f"Found the following new articles matching your keywords ({current_time_str}):\n\n"
                for headline, link in all_relevant_articles_this_run.items():
                    email_body += f"- {headline}\n  Link: {link}\n\n"
                send_email(email_subject, email_body)

            # --- Wait before next check ---
            check_interval_seconds = 3600 # Check every hour
            safe_print(f"\nWaiting for {check_interval_seconds // 60} minutes before next check...")
            time.sleep(check_interval_seconds)

    except KeyboardInterrupt:
        safe_print("\nStopping news monitor.")
    except Exception as e:
        safe_print(f"\n--- UNEXPECTED ERROR in main loop ---")
        safe_print(f"An error occurred: {e}")
        import traceback
        safe_print("Traceback:")
        safe_print(traceback.format_exc())
        safe_print("------------------------")

