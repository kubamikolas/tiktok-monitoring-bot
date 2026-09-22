import json
import os
import requests
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from config import WATCHED_ACCOUNTS

load_dotenv()

STATE_FILE = "state.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
        },
        timeout=30,
    )
    response.raise_for_status()


def is_new_video(state, username, video_id):
    videos = state.get(username, [])
    return video_id not in videos


def remember_video(state, username, video_id):
    if username not in state:
        state[username] = []
    if video_id not in state[username]:
        state[username].append(video_id)


async def check_account(page, username, state):
    print(f"Kontroluji účet: @{username}")
    url = f"https://www.tiktok.com/@{username}"
    
    new_videos_found = 0
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(6000) # Počkáme na načtení prvků stránky
        
        # Získání odkazů na videa pomocí Playwrightu
        links = await page.locator('a[href*="/video/"]').evaluate_all(
            """els => els.map(e => e.href)"""
        )

        for link in links:
            if "/video/" in link:
                parts = link.split("/video/")
                if len(parts) == 2:
                    video_id = parts[1].split("?")[0]
                    
                    if is_new_video(state, username, video_id):
                        print(f"  -> Nalezeno nové video ID: {video_id}")
                        
                        remember_video(state, username, video_id)
                        
                        # Odeslání zprávy na Telegram o novém videu
                        video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                        send_telegram(
                            f"🎬 Nové TikTok video!\n\n"
                            f"👤 @{username}\n\n"
                            f"🔗 {video_url}"
                        )
                        new_videos_found += 1
                        
        print(f"  -> Hotovo pro @{username}, nové videa: {new_videos_found}")

    except Exception as e:
        print(f"  ❌ Chyba při kontrole @{username}: {e}")

    return new_videos_found


async def main():
    state = load_state()

    print("================================")
    print(" TikTok Auto Monitor Bot")
    print("================================")
    print(f"Sledovaných účtů: {len(WATCHED_ACCOUNTS)}")
    print()

    total_new_videos = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
        )

        for username in WATCHED_ACCOUNTS:
            new_found = await check_account(page, username, state)
            total_new_videos += new_found
            # Menší pauza mezi účty, aby TikTok botu nezablokoval přístup
            await asyncio.sleep(3)

        await browser.close()

    save_state(state)
    
    # Odeslání souhrnné zprávy o proběhlé kontrole na Telegram
    try:
        send_telegram(
            f"🤖 Právě jsem zkontroloval všech {len(WATCHED_ACCOUNTS)} účtů.\n"
            f"✨ Nových videí nalezeno: {total_new_videos}"
        )
    except Exception as e:
        print(f"  ❌ Chyba při odesílání souhrnu na Telegram: {e}")

    print("\n✅ Kontrola všech účtů dokončena a stav byl uložen do state.json.")


if __name__ == "__main__":
    asyncio.run(main())