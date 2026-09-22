import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        )

        print("Otevírám TikTok...")

        await page.goto(
            "https://www.tiktok.com/@mar3lglive",
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_timeout(8000)

        title = await page.title()
        url = page.url
        text = await page.locator("body").inner_text()

        print("\n--- STRÁNKA ---")
        print("Title:", title)
        print("URL:", url)

        print("\n--- TEXT STRÁNKY ---")
        print(text[:5000])

        print("\n--- VIDEO ODKAZY ---")

        links = await page.locator('a[href*="/video/"]').evaluate_all(
            """els => els.map(e => e.href)"""
        )

        print("Počet:", len(links))

        for link in links[:20]:
            print(link)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())