from fastapi import FastAPI
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from typing import List, Dict

app = FastAPI()

CATEGORIES = {
    "lietuvoje": "https://www.lrt.lt/naujienos/lietuvoje",
    "verslas": "https://www.lrt.lt/naujienos/verslas",
    "pasaulyje": "https://www.lrt.lt/naujienos/pasaulyje",
    "eismas": "https://www.lrt.lt/naujienos/eismas",
    "mokslas-ir-it": "https://www.lrt.lt/naujienos/mokslas-ir-it"
}

BASE_URL = "https://www.lrt.lt"


def parse_category_page(category_name: str, url: str) -> List[Dict]:
    articles = []
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Randa visus 5 straipsnius pagal .row > .col struktūrą
        article_blocks = soup.select("div.row > div.col")
        for rank, block in enumerate(article_blocks[:5], start=1):
            try:
                title_tag = block.select_one("h3.news__title > a")
                title = title_tag.text.strip()
                relative_url = title_tag.get("href", "")
                full_url = BASE_URL + relative_url

                published = block.select_one("span.info-block__text")
                published_text = published.text.strip() if published else None

                articles.append({
                    "title": title,
                    "url": full_url,
                    "published": published_text,
                    "category": category_name,
                    "rank": rank
                })
            except Exception as e:
                continue  # praleidžiam konkrečią blogą struktūrą

    except Exception as e:
        # Logika, jei visa kategorija nepavyksta
        return [{
            "title": None,
            "url": None,
            "published": None,
            "category": category_name,
            "rank": None,
            "error": str(e)
        }]
    
    return articles


@app.get("/lrt-most-read")
def get_lrt_most_read():
    all_articles = []
    errors = {}

    for category, url in CATEGORIES.items():
        parsed = parse_category_page(category, url)

        if parsed and parsed[0].get("error"):
            errors[category] = parsed[0]["error"]
        else:
            errors[category] = None
            all_articles.extend(parsed)

    return {
        "success": True,
        "scraped_at": datetime.utcnow().isoformat(),
        "articles": all_articles,
        "errors": errors
    }
