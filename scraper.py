import requests
from bs4 import BeautifulSoup
import time
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
BASE = "https://www.webster.edu"
CATALOG_URL = "https://www.webster.edu/catalog/current/undergraduate-catalog/index.html"

def scrape_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return "", []
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get all links on this page
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/catalog/current/undergraduate-catalog/"):
                links.append(BASE + href)
            elif href.startswith("http") and "webster.edu/catalog/current/undergraduate-catalog" in href:
                links.append(href)
        
        # Clean text
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 15]
        return "\n".join(lines), links
    except Exception as e:
        print(f"  Error: {e}")
        return "", []

def scrape_catalog():
    os.makedirs("data", exist_ok=True)
    visited = set()
    all_text = ""
    to_visit = [CATALOG_URL]

    print("Scraping Webster Undergraduate Catalog...")
    print("This will collect ALL majors, courses and requirements\n")

    while to_visit and len(visited) < 300:
        url = to_visit.pop(0)
        if "#" in url:
            url = url.split("#")[0]
        if url in visited:
            continue

        print(f"[{len(visited)+1}] {url}")
        text, links = scrape_page(url)
        visited.add(url)

        if text:
            all_text += f"\n\n{'='*60}\nSOURCE: {url}\n{'='*60}\n{text}"
            print(f"  ✅ {len(text)} chars | {len(links)} new links found")

        for link in links:
            clean = link.split("#")[0]
            if clean not in visited and clean not in to_visit:
                to_visit.append(clean)

        time.sleep(0.3)

    output = "data/webster_catalog.txt"
    with open(output, "w", encoding="utf-8") as f:
        f.write(all_text)

    size_kb = os.path.getsize(output) / 1024
    print(f"\n✅ Done! Scraped {len(visited)} pages")
    print(f"📄 File size: {size_kb:.1f} KB")
    print(f"💾 Saved to: {output}")
    print(f"\n🚀 Now run: python3 setup_documents.py")

if __name__ == "__main__":
    scrape_catalog()
