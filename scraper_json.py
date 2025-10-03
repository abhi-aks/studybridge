import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

url = "https://www.th-bingen.de/en"

visited_urls = set()
website_data = {
    "pages": [],  # List of all pages
    "metadata": {
        "last_updated": "",
        "total_pages": 0,
        "base_url": ""
    }
}


def scrape_website():
    website_data["metadata"]["base_url"] = url
    unvisited_urls = {url}

    while unvisited_urls:
        current_url = unvisited_urls.pop()

        if current_url in visited_urls:
            continue

        try:
            bs_html = get_bs_html(current_url)
            text_content = ' '.join([clean_text(p.get_text(strip=True))
                                     for p in bs_html.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])])
            page_data = {
                "url": current_url,
                "title": bs_html.title.string if bs_html.title else "No title",
                "timestamp": datetime.now().isoformat(),
                "content": text_content,
                "type": "webpage"
            }

            website_data["pages"].append(page_data)
            visited_urls.add(current_url)

            new_urls = extract_urls(bs_html, current_url)
            unvisited_urls.update(set(new_urls) - visited_urls)

            website_data["metadata"]["last_updated"] = datetime.now().isoformat()
            website_data["metadata"]["total_pages"] = len(website_data["pages"])

            print(f"Scraped: {current_url}")

        except:
            print(f"Error scraping {current_url}")
            visited_urls.add(current_url)

        time.sleep(1)

    return  website_data


def get_bs_html(current_url):
    # Add headers to mimic a browser request
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(current_url, headers=header)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except:
        print(f"Error fetching {current_url}")
        return None


def extract_urls(html, current_url):
    urls = set()
    base_domain = urlparse(url).netloc

    # find links
    for link in html.findAll('a', href=True):
        href = link['href']
        absolute_url = urljoin(current_url, href)
        parsed = urlparse(absolute_url)

        # same domain + http(s) protocol + no fragments
        if(parsed.netloc == base_domain and
            parsed.scheme in ["http", "https"] and
            not parsed.fragment and
                ('/en/' in parsed.path or parsed.path.startswith('/en'))):  # remove this when only checking th-bingen.de

            clean_url = absolute_url.rstrip("/")
            urls.add(clean_url)

    return list(urls)


def clean_text(text):
    cleaned = text.replace('\xad', '').replace('\u00ad', '')  # Remove soft hyphens
    cleaned = ' '.join(cleaned.split())  # Normalise whitespace
    return cleaned


def save_results(filename="website_data_en.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(website_data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    scrape_website()
    save_results()

