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
    # Bilinen çalışan adresler. Eğer site yine domain değiştirirse buraya ekleyebilirsin.
    test_urls = [
        "https://www.selcuksportshd14e17ba2ad.xyz/",
        "https://www.selcuksportshd.is/",
        "https://www.selcuksportshd0.xyz/"
    ]
    for url in test_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "uxsyplayer" in res.text:
                print(f"✅ Aktif domain bulundu: {url}")
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
        name = name_div.get_text(strip=True) if name_div else "Bilinmeyen Kanal"

        id_match = re.search(r'id=([a-zA-Z0-9_-]+)', data_url)
        if not id_match:
            continue
        channel_id = id_match.group(1)

        links.append({"url": data_url, "name": name, "id": channel_id})

    return links

def normalize_tvg_id(name):
    rep = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O'}
    for k,v in rep.items():
        name = name.replace(k, v)
    name = name.replace(" ", "-").replace(":", "-")
    name = re.sub(r"[^a-zA-Z0-9\-]", "", name)
    return name.lower()

async def create_m3u(filename="selcukk.m3u"):
    print("🔍 Domain aranıyor...")
    domain, html = find_active_domain()

    if not html:
        print("❌ Çalışan domain bulunamadı!")
        return

    referer = domain
    players = get_player_links(html)

    if not players:
        print("❌ Player link yok!")
        return

    print(f"📺 {len(players)} kanal bulundu. Hızlı modda test ediliyor...\n")

    m3u = ["#EXTM3U"]
    ok = 0
    benzersiz = set()

    async with async_playwright() as p:
        # Tarayıcıyı bir kez başlatıyoruz
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            extra_http_headers={"Referer": referer}
        )

        # Reklam ve gereksiz resimleri engelle (İşlemi çok hızlandırır)
        await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())

        for ch in players:
            if ch["id"] in benzersiz:
                continue

            print(f"⏳ İşleniyor: {ch['name']}")
            captured_urls = []
            
            page = await context.new_page()
            
            # Sadece .m3u8 isteklerini dinle
            page.on("request", lambda req: captured_urls.append(req.url) if ".m3u8" in req.url and "cloudflare" not in req.url else None)

            try:
                # DOM yüklendiğinde devam et, arkadaki reklamları bekleme
                await page.goto(ch["url"], wait_until="domcontentloaded", timeout=8000)
                # Oynatıcının m3u8 isteğini atması için 1 saniye bekle
                await page.wait_for_timeout(1000) 

                m3u8 = captured_urls[0] if captured_urls else None

                if m3u8:
                    tvg_id = normalize_tvg_id(ch["name"])
                    m3u.append(f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="Sell spor+sec izle",{ch["name"]}')
                    m3u.append(f"#EXTVLCOPT:http-referrer={referer}")
                    m3u.append(f"#EXTVLCOPT:http-user-agent={HEADERS['User-Agent']}")
                    m3u.append(m3u8)
                    ok += 1
                    benzersiz.add(ch["id"])
                    print(f"🎯 M3U8 bulundu: {m3u8}")
                else:
                    print(f"❌ Link bulunamadı: {ch['name']}")
            except Exception as e:
                print(f"❌ Hata/Timeout: {ch['name']}")
            finally:
                await page.close()

        await browser.close()

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))

    print(f"\n✅ M3U oluşturuldu: {filename}")
    print(f"📊 Başarılı: {ok}/{len(players)}")

if __name__ == "__main__":
    asyncio.run(create_m3u())
