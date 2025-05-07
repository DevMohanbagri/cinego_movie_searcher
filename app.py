import os
import requests
import xml.etree.ElementTree as ET
import re
import time
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
BASE_URL = "https://cinego.tv/sitemap-movie-{}.xml"
SITEMAP_RANGE = range(1, 62)  # 1 to 61 inclusive
SAVE_DIR = "sitemaps"
INDEX_FILE = "url_index.txt"
RETRY_COUNT = 3
BACKOFF_FACTOR = 2
REQUEST_DELAY = 2  # Increased delay between requests in seconds
MAX_ATTEMPTS = 3  # Additional retry attempts for each sitemap

def create_save_dir():
    """Create directory to store sitemaps if it doesn't exist."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

def setup_session():
    """Set up a requests session with retry logic and user-agent."""
    session = requests.Session()
    retries = Retry(
        total=RETRY_COUNT,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # Add a user-agent to make requests look more legitimate
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    return session

def download_sitemap(sitemap_number, session):
    """Download a single sitemap and save it locally with retries."""
    url = BASE_URL.format(sitemap_number)
    file_path = os.path.join(SAVE_DIR, f"sitemap-movie-{sitemap_number}.xml")
    
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"Downloaded sitemap {sitemap_number} to {file_path}")
            return file_path
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}/{MAX_ATTEMPTS} failed for sitemap {sitemap_number}: {e}")
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_FACTOR * (2 ** attempt))  # Exponential backoff
            else:
                print(f"Failed to download sitemap {sitemap_number} after {MAX_ATTEMPTS} attempts.")
                return None

def extract_urls(sitemap_file):
    """Extract URLs from a sitemap XML file."""
    urls = []
    try:
        tree = ET.parse(sitemap_file)
        root = tree.getroot()
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_elem in root.findall('ns:url/ns:loc', namespace):
            urls.append(url_elem.text)
        return urls
    except ET.ParseError as e:
        print(f"Error parsing {sitemap_file}: {e}")
        return []

def are_all_sitemaps_downloaded():
    """Check if all sitemaps (1 to 61) are downloaded."""
    for i in SITEMAP_RANGE:
        sitemap_file = os.path.join(SAVE_DIR, f"sitemap-movie-{i}.xml")
        if not os.path.exists(sitemap_file):
            return False
    return True

def build_url_index():
    """Build a local URL index from sitemaps, downloading only missing ones."""
    create_save_dir()
    
    # Check if all sitemaps are already downloaded
    if are_all_sitemaps_downloaded():
        print("All sitemaps are already downloaded.")
        # If index file doesn't exist, build it from existing sitemaps
        if not os.path.exists(INDEX_FILE):
            all_urls = []
            for i in SITEMAP_RANGE:
                sitemap_file = os.path.join(SAVE_DIR, f"sitemap-movie-{i}.xml")
                urls = extract_urls(sitemap_file)
                all_urls.extend(urls)
            with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                for url in all_urls:
                    f.write(url + '\n')
            print(f"Saved {len(all_urls)} URLs to {INDEX_FILE}")
        else:
            print("Index file already exists.")
        return

    # Download missing sitemaps and build index
    all_urls = []
    session = setup_session()
    
    for i in SITEMAP_RANGE:
        sitemap_file = os.path.join(SAVE_DIR, f"sitemap-movie-{i}.xml")
        if not os.path.exists(sitemap_file):
            sitemap_file = download_sitemap(i, session)
            time.sleep(REQUEST_DELAY)  # Delay to avoid overwhelming the server
        if sitemap_file:
            urls = extract_urls(sitemap_file)
            all_urls.extend(urls)
    
    # Save URLs to index file
    if all_urls:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            for url in all_urls:
                f.write(url + '\n')
        print(f"Saved {len(all_urls)} URLs to {INDEX_FILE}")

def normalize_movie_name(query):
    """Convert movie name to URL-friendly format (replace spaces with hyphens)."""
    return re.sub(r'\s+', '-', query.strip().lower())

def search_urls(movie_name):
    """Search for URLs containing the movie name in the URL path."""
    if not movie_name:
        return []
    
    # Normalize the movie name for searching
    normalized_name = normalize_movie_name(movie_name)
    matches = []
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                # Extract the path from the URL
                parsed_url = urlparse(url)
                path = parsed_url.path.lower()
                # Check if the normalized movie name is in the path
                if normalized_name in path:
                    matches.append(url)
        return matches
    except FileNotFoundError:
        print("URL index not found. Please ensure sitemaps are downloaded.")
        return []

def main():
    """Main function to run the application."""
    # Build index if necessary (downloads missing sitemaps)
    build_url_index()
    
    # Prompt for movie name and search
    movie_name = input("Enter movie name (e.g., The Vampire Diaries): ").strip()
    if not movie_name:
        print("Movie name cannot be empty.")
        return
    matches = search_urls(movie_name)
    if matches:
        print(f"Found {len(matches)} matching URLs for '{movie_name}':")
        for url in matches:
            print(url)
    else:
        print(f"No matches found for '{movie_name}'.")

if __name__ == "__main__":
    main()
