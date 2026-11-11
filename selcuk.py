import re
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
}

def find_active_domain():
    import requests
    test_urls = [
        "https://www.selcuksportshd14e17ba2ad.xyz/",
        "https://www.selcuksportshd.is/",
        "https://www.selcuksportshd0.xyz/"
    ]
    for url in test_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "data-url" in res.text:
                print(f"[+] Aktif Domain: {url}")
                return url, res.text
        except:
            continue
    return None, None

async def get_m3u8_playwright(iframe_url, referer, channel_id):
    """Playwright ile iframe sayfasını açar ve ağ trafiğinden m3u8 yakalar."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            extra_http_headers={"Referer": referer}
        )
        page = await context.new_page()

        captured_urls = []

        def handle_request(request):
            url = request.url
            if ".m3u8" in url and "cloudflare" not in url and "beacon" not in url:
                captured_urls.append(url)

        page.on("request", handle_request)

        try:
            await page.goto(iframe_url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(3000)

            if captured_urls:
                await browser.close()
                return captured_urls[0]

            # Sayfa içeriğinden de ara (belki JS değişkende saklıdır)
            content = await page.content()
            for m in re.finditer(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', content):
                url = m.group(1)
                if "cloudflare" not in url and "beacon" not in url:
                    await browser.close()
                    return url

        except Exception as e:
            pass
        finally:
            await browser.close()
    return None

async def main():
    domain, html = find_active_domain()
    if not domain:
        print("[-] Domain bulunamadı.")
        return

    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("a", attrs={"data-url": True})

    m3u_lines = ["#EXTM3U"]
    basarili = 0

    print(f"[*] {len(items)} kanal test ediliyor...\n")

    for item in items:
        raw_url = item["data-url"]
        if "gecersiz" in raw_url or not raw_url.startswith("http") or "Undefined" in raw_url:
            continue

        name_div = item.find("div", class_="name")
        name = name_div.get_text(strip=True) if name_div else "Bilinmeyen"

        id_match = re.search(r'id=([a-zA-Z0-9_-]+)', raw_url)
        channel_id = id_match.group(1) if id_match else None

        if not channel_id:
            print(f"[✗] {name} (ID yok)")
            continue

        link = await get_m3u8_playwright(raw_url, domain, channel_id)

        if link:
            print(f"[✓] {name} -> {link}")
            m3u_lines.append(f'#EXTINF:-1, {name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={domain}')
            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_lines.append(link)
            basarili += 1
        else:
            print(f"[✗] {name} (Link yok)")

    with open("selcukk.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"\n[✓] {basarili} kanal kaydedildi. Dosya: selcukk.m3u")

if __name__ == "__main__":
    asyncio.run(main())
