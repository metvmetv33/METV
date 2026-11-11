import re
import asyncio
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

def find_active_domain():
    test_urls = [
        "https://www.selcuksportshd14e17ba2ad.xyz/",
        "https://www.selcuksportshd.is/",
        "https://www.selcuksportshd0.xyz/"
    ]
    for url in test_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "uxsyplayer" in res.text:
                print(f"✅ Aktif domain: {url}")
                return url, res.text
        except:
            continue
    return None, None

def get_player_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", attrs={"data-url": True}):
        data_url = a["data-url"].strip()
        if "gecersiz" in data_url or not data_url.startswith("http") or "Undefined" in data_url:
            continue
        name_div = a.find("div", class_="name")
        name = name_div.get_text(strip=True) if name_div else "Bilinmeyen"
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)', data_url)
        if not id_match:
            continue
        links.append({"url": data_url, "name": name, "id": id_match.group(1)})
    return links

def normalize_tvg_id(name):
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = name.replace(" ", "-").replace(":", "-")
    name = re.sub(r"[^a-zA-Z0-9\-]", "", name)
    return name.lower()

async def create_m3u(filename="selcukk.m3u"):
    domain, html = find_active_domain()
    if not html:
        print("❌ Domain bulunamadı!")
        return

    players = get_player_links(html)
    if not players:
        print("❌ Kanal yok!")
        return

    print(f"📺 {len(players)} kanal test ediliyor (yavaş mod)...\n")

    m3u = ["#EXTM3U"]
    ok = 0
    benzersiz = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Reklam engelleme YOK, her şeyin yüklenmesine izin ver
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            extra_http_headers={"Referer": domain}
        )

        for ch in players:
            if ch["id"] in benzersiz:
                continue

            print(f"⏳ {ch['name']}")
            captured = []

            page = await context.new_page()
            # Tüm m3u8 içeren istekleri yakala, cloudflare olmasın yeter
            page.on("request", lambda req: captured.append(req.url) if ".m3u8" in req.url and "cloudflare" not in req.url else None)

            try:
                # Ağın tamamen durulmasını bekle (timeout 20 sn)
                await page.goto(ch["url"], wait_until="networkidle", timeout=20000)
                # Ekstra bekleme: oynatıcı geç başlatabilir
                await page.wait_for_timeout(4000)

                if captured:
                    # İlk yakalanan m3u8'i al
                    m3u8 = captured[0]
                    tvg_id = normalize_tvg_id(ch["name"])
                    m3u.append(f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="Sell spor+sec izle",{ch["name"]}')
                    m3u.append(f"#EXTVLCOPT:http-referrer={domain}")
                    m3u.append(f"#EXTVLCOPT:http-user-agent={HEADERS['User-Agent']}")
                    m3u.append(m3u8)
                    ok += 1
                    benzersiz.add(ch["id"])
                    print(f"🎯 {m3u8}")
                else:
                    print(f"❌ Link yok")
            except Exception as e:
                print(f"❌ Hata: {ch['name']}")
            finally:
                await page.close()

        await browser.close()

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))

    print(f"\n✅ {ok}/{len(players)} kanal kaydedildi: {filename}")

if __name__ == "__main__":
    asyncio.run(create_m3u())
