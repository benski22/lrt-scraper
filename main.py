from fastapi import FastAPI
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI()

@app.get("/lrt-most-read")
def scrape_lrt():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.lrt.lt/naujienos/lietuvoje")
        page.wait_for_selector("#news-feed-most-read-content-110343")
        soup = BeautifulSoup(page.content(), "html.parser")

        cards = soup.select("#news-feed-most-read-content-110343 div.news")
        result = []
        for card in cards[:5]:
            link = card.select_one("h3.news__title a")
            if not link:
                continue
            url = "https://www.lrt.lt" + link["href"]
            title = link.text.strip()
            pub = card.select_one(".info-block span")
            published = pub["title"] if pub else ""
            page.goto(url)
            soup_full = BeautifulSoup(page.content(), "html.parser")
            full_text = "\n".join([p.text.strip() for p in soup_full.select("div.article__body p")])
            result.append({"title": title, "url": url, "published": published, "full_text": full_text})
        browser.close()
        return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
