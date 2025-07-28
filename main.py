from fastapi import FastAPI
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI()

@app.get("/lrt-most-read")
def scrape_lrt():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.lrt.lt/naujienos/lietuvoje", timeout=20000)

            # Paspaudžia ant "Skaitomiausi" tab'o
            page.click("a[href^='#news-feed-most-read-content']", timeout=5000)

            # Palaukia, kol atsidaro aktyvus tab'as su straipsniais
            page.wait_for_selector("div.tab-pane.active.show div.col", timeout=10000)

            soup = BeautifulSoup(page.content(), "html.parser")
            articles = soup.select("div.tab-pane.active.show div.col")

            result = []
            for card in articles[:5]:
                link_tag = card.select_one("a.media-block__link")
                title_tag = link_tag["title"] if link_tag else None
                href = link_tag["href"] if link_tag else None

                date_tag = card.select_one("span.info-block__time-before")
                published = date_tag.text.strip() if date_tag else ""

                if not title_tag or not href:
                    continue

                result.append({
                    "title": title_tag,
                    "url": "https://www.lrt.lt" + href,
                    "published": published
                })

            browser.close()
            return result

    except PlaywrightTimeoutError:
        return {"error": "Nepavyko rasti 'most read' blokelio per 10–20 s."}
