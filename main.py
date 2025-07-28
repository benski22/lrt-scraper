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
            page.wait_for_timeout(3000)  # leidžiam JS pilnai įkelti tab'us

            # Tiesiogiai imam HTML iš aktyvaus tab-pane (Skaitomiausi)
            content_html = page.locator("div.tab-pane.show.active").inner_html()
            soup = BeautifulSoup(content_html, "html.parser")
            cards = soup.select("div.col")

            result = []
            for card in cards[:5]:
                link = card.select_one("a.media-block__link")
                if not link:
                    continue
                url = "https://www.lrt.lt" + link["href"]
                title = link.get("title", "").strip()

                time_span = card.select_one("span.info-block__time-before")
                published = time_span.text.strip() if time_span else ""

                # Atidarom straipsnį ir imam pilną tekstą
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
