# scraping.py
"""
Scraping script for Atlan documentation.
Fetches URLs from sitemaps, extracts main content, and saves cleaned docs to CSV.
"""

import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd


# ---- Step 1: Fetch URLs from sitemap ----
def get_urls_from_sitemap(sitemap_url):
    resp = requests.get(sitemap_url)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [url.find("sm:loc", ns).text for url in root.findall("sm:url", ns)]
    return urls


sitemaps = [
    "https://docs.atlan.com/sitemap.xml",
    "https://developer.atlan.com/sitemap.xml",
]

all_urls = []
for sm in sitemaps:
    all_urls.extend(get_urls_from_sitemap(sm))

print(f"Found {len(all_urls)} URLs total")
print("Sample URLs:", all_urls[:5])


# ---- Step 2: Extract main content from each page ----
def extract_main_content(url):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Most MkDocs pages put docs inside <article>
        article = soup.find("article")
        if article:
            text = article.get_text(" ", strip=True)
        else:
            # fallback: get body text
            text = soup.body.get_text(" ", strip=True)

        return text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


# ---- Step 3: Filter URLs ----
def is_useful_url(url):
    bad_patterns = ["/search", "/tags$"]
    return not any(url.endswith(bp) or url.endswith(bp + "/") for bp in bad_patterns)


# ---- Step 4: Clean & Save ----
filtered_urls = [u for u in all_urls if is_useful_url(u)]
print(f"Filtered down to {len(filtered_urls)} useful URLs")

data = []
for url in filtered_urls:
    content = extract_main_content(url)
    data.append(
        {
            "url": url,
            "content": content,
            "content_length": len(content),
            "preview": content[:200],
        }
    )

df = pd.DataFrame(data)
df.to_csv("atlan_docs_cleaned.csv", index=False)
print("Saved cleaned docs -> atlan_docs_cleaned.csv")
print(df.head(10))
