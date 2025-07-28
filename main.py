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
            page.goto("https://www.lrt.lt", timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)  # laukiam 2 sekundes, kad JS suveiktų

            # Paspaudžiam ant "Skaitomiausi" tab (jei jis dar neaktyvus)
            try:
                page.click("a.nav-link[href^='#news-feed-most-read-content']", timeout=5000)
                page.wait_for_timeout(1000)
            except:
                pass  # jei jau aktyvus, leidžiam testuoti toliau

            # Laukiam, kol įsikraus aktyvus "Skaitomiausi" blokas
            page.wait_for_selector("div.tab-pane.show.active", timeout=30000)

            # Ištraukiam tik aktyvios sekcijos HTML
            html = page.locator("div.tab-pane.show.active").inner_html()
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.col")

            if not cards:
                return {"error": "Nerasta jokių skaitomiausių straipsnių."}

            result = []
            for card in cards[:5]:
                link = card.select_one("a.media-block__link")
                if not link:
                    continue
                url = "https://www.lrt.lt" + link.get("href", "")
                title = link.get("title", "").strip()

                time_span = card.select_one("span.info-block__time-before")
                published = time_span.text.strip() if time_span else ""

                # Atidarom straipsnį ir imam visą tekstą
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
