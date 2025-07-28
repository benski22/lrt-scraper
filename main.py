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
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                viewport={"width": 1280, "height": 800}
            )

            # Eiti į pagrindinį puslapį
            page.goto("https://www.lrt.lt", timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(5000)  # padidintas laukimas

            # Debug: parodyti visą puslapio HTML
            print("=== page.content START ===")
            print(page.content())
            print("=== page.content END ===")

            # Debug: parodyti visus div ID, prasidedančius nuo news-feed
            ids = page.evaluate("""() => {
                return Array.from(document.querySelectorAll("div"))
                            .map(d => d.id)
                            .filter(id => id && id.startsWith("news-feed-most-read-content-"))
            }""")
            print("Rasti blokų ID:", ids)

            # Surandam elementą DOM'e
            locator = page.locator("div[id^='news-feed-most-read-content-']")
            element_count = locator.count()
            if element_count == 0:
                return {"error": "Nerasta skaitomiausių naujienų blokelio."}

            html = locator.first.inner_html()
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.col")

            if not cards:
                return {"error": "Nerasta skaitomiausių naujienų straipsnių."}

            result = []
            for card in cards[:10]:
                link = card.select_one("a.media-block__link")
                if not link:
                    continue
                url = "https://www.lrt.lt" + link["href"]
                title = link.get("title", "").strip()

                time_span = card.select_one("span.info-block__time-before")
                published = time_span.text.strip() if time_span else ""

                # Straipsnio tekstas
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
