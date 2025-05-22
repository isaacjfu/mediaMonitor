import requests
from urllib.parse import urljoin
import json
import time

# --- Selenium Imports ---
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException


def fetch_html_with_selenium(url, site_name):
    """Fetches dynamically loaded HTML content from a given URL using Selenium."""
    driver = None # Initialize driver to None
    html_content = None # Initialize html_content
    # Define a filename for saving the source code
    source_filename = f"html/{site_name}_source_sel.html"
    try:
        # Setup Chrome options (headless recommended for background execution)
        options = uc.ChromeOptions()
        options.binary_location = "/usr/bin/chromium"
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

        # Initialize WebDriver (assuming chromedriver is in PATH)
        # If not in PATH, use: driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = uc.Chrome(options=options, headless = True, use_subprocess = True)
        driver.implicitly_wait(5) # Basic implicit wait

        print(f"Loading URL with Selenium: {url}")
        driver.get(url)

        time.sleep(15)

        # Get the page source *after* JavaScript has potentially run
        html_content = driver.page_source
        print(f"Successfully fetched HTML for {url}")

        # --- Save the fetched HTML for debugging ---
        try:
            with open(source_filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Saved fetched HTML source to '{source_filename}'")
        except Exception as save_e:
            print(f"Could not save HTML source to file: {save_e}")
        # --- End Save HTML ---
        return html_content

    except TimeoutException:
        print(f"Error: Timed out waiting for element '{wait_selector_str}' on {url}. Page might not have loaded correctly or selector is wrong.")
        # Try to get and save page source even on timeout for debugging
        if driver:
             try:
                 html_content = driver.page_source
                 with open(source_filename, "w", encoding="utf-8") as f:
                     f.write(html_content if html_content else "")
                 print(f"Saved HTML source (on timeout) to '{source_filename}' - PLEASE INSPECT THIS FILE.")
                 return html_content # Return potentially incomplete HTML
             except Exception as save_e:
                 print(f"Could not save HTML source to file after timeout: {save_e}")
        return None # Indicate failure
    except WebDriverException as e:
        print(f"Error during Selenium fetch for {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Selenium fetch for {url}: {e}")
        return None
    finally:
        # Ensure the browser is closed even if errors occur
        if driver:
            print("Closing Selenium browser.")
            driver.quit()

def fetch_html_without_selenium(url, site_name):
     """Fetches HTML content from a given URL."""
     source_filename = f"html/{site_name}_source.html"
     try:
         # Send an HTTP GET request to the URL
         # Include a User-Agent header to mimic a browser visit
         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
         response = requests.get(url, headers=headers, timeout=10) # Added timeout
         response.encoding = 'gbk'
         #response.encoding = 'gb2312'
         response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
         with open(source_filename,'w') as f:
             f.write(response.text)
         return response.text
     except requests.exceptions.RequestException as e:
         print(f"Error fetching {url}: {e}")
         return None


try:
    with open('config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        NEWS_WEBSITES = data['websites']
except FileNotFoundError:
    print('Error: The file config.json was not found')
except json.JSONDecodeError:
    print('Error: Invalid JSON found in config.json')
except Exception as e:
    print("Error: {e}")

for website in NEWS_WEBSITES:
    if website['rss'] != 1:
        print(f"Trying to fetch for {website['name']}")
        print("Fetching only using requests")
        fetch_html_without_selenium(website['url'],website['name'])
        print("Fetching with selenium")
        fetch_html_with_selenium(website['url'],website['name'])
