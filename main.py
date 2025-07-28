from fastapi import FastAPI
from playwright.sync_api import sync_playwright
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

            # Paspaudžiam ant "Skaitomiausi" tab
            page.click("a[href^='#news-feed-most-read-content']", timeout=5000)

            # Laukiam, kol aktyvus blokas įsikraus
            page.wait_for_selector("div.tab-pane.show.active div.col", timeout=20000)

            # Paimam puslapio HTML
            soup = BeautifulSoup(page.content(), "html.parser")
            cards = soup.select("div.tab-pane.show.active div.col")

            result = []
            for card in cards[:5]:
                link = card.select_one("a.media-block__link")
                if not link:
                    continue
                url = "https://www.lrt.lt" + link["href"]
                title = link.get("title", "").strip()

                time_span = card.select_one("span.info-block__time-before")
                published = time_span.text.strip() if time_span else ""

                # Atidarom straipsnį ir traukiam visą tekstą
                page.goto(url, timeout=15000)
                soup_full = BeautifulSoup(page.content(), "html.parser")
                full_text = "\n".join([p.text.strip() for p in soup_full.select("div.article__body p")])
                result.append({
                    "title": title,
                    "url": url,
                    "published": published,
                    "full_text": full_text
                })

            browser.close()
            return result
    except Exception as e:
        return {"error": f"Nepavyko nuskaityti LRT: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
