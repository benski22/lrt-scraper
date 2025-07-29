from fastapi import FastAPI, Query
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI()

@app.get("/lrt-most-read")
def scrape_lrt(limit: int = Query(10, ge=1, le=10)):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                viewport={"width": 1280, "height": 800}
            )

            # Eiti į LRT pagrindinį puslapį
            page.goto("https://www.lrt.lt", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)  # daugiau laiko JS generavimui

            # Ieškom blokelio DOM'e
            locator = page.locator("div[id^='news-feed-most-read-content-']")
            if locator.count() == 0:
                return {"error": "Nerasta skaitomiausių naujienų blokelio."}

            try:
                html = locator.first.inner_html()
            except:
                return {"error": "Nepavyko gauti skaitomiausių blokelio HTML."}

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.col")
            if not cards:
                return {"error": "Nerasta skaitomiausių naujienų straipsnių."}

            result = []
            for card in cards[:limit]:
                link = card.select_one("a.media-block__link")
                if not link:
                    continue
                url = "https://www.lrt.lt" + link["href"]
                title = link.get("title", "").strip()

                time_span = card.select_one("span.info-block__time-before")
                published = time_span.text.strip() if time_span else ""

                result.append({
                    "title": title,
                    "url": url,
                    "published": published
                })

            browser.close()
            return result

    except Exception as e:
        return {"error": f"Nepavyko nuskaityti LRT: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
