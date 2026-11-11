import re
import asyncio
import requests
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}

def find_active_domain():
    """Sitenin güncel çalışan domainini bulur (bilinen adresler üzerinden)."""
    test_urls = [
        "https://www.selcuksportshd14e17ba2ad.xyz/",
        "https://www.selcuksportshd.is/",
        "https://www.selcuksportshd0.xyz/"
    ]
    for url in test_urls:
        try:
            res = requests.get(url, headers=headers, timeout=10, verify=False)
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

        # Geçersiz linkleri atla
        if "gecersiz" in data_url or not data_url.startswith("http") or "Undefined" in data_url:
            continue

        name_div = a.find("div", class_="name")
        name = name_div.get_text(strip=True) if name_div else "Bilinmeyen Kanal"

        # Kanal ID'sini çek
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)', data_url)
        if not id_match:
            continue
        channel_id = id_match.group(1)

        links.append({"url": data_url, "name": name, "id": channel_id})

    return links

async def get_m3u8_playwright(iframe_url, referer, channel_id):
    """Playwright ile iframe sayfasını açar ve ağ trafiğinden m3u8 yakalar."""
    captured_urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=headers["User-Agent"],
            extra_http_headers={"Referer": referer}
        )
        page = await context.new_page()

        def handle_request(request):
            url = request.url
            if ".m3u8" in url and "cloudflare" not in url and "beacon" not in url:
                captured_urls.append(url)

        page.on("request", handle_request)

        try:
            await page.goto(iframe_url, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1500)

            if captured_urls:
                return captured_urls[0]

            # Sayfa içeriğinden de ara
            content = await page.content()
            for m in re.finditer(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', content):
                url = m.group(1)
                if "cloudflare" not in url and "beacon" not in url:
                    return url
        except:
            pass
        finally:
            await browser.close()

    return None

def normalize_tvg_id(name):
    rep = {
        'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G',
        'ü':'u','Ü':'U','ö':'o','Ö':'O'
    }
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

    print(f"📺 {len(players)} kanal bulundu")

    m3u = ["#EXTM3U"]
    ok = 0
    benzersiz = set()

    # Tek bir tarayıcı aç, tüm kanalları aynı tarayıcı içinde gez
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=headers["User-Agent"],
            extra_http_headers={"Referer": referer}
        )

        for ch in players:
            # Aynı kanalı tekrar test etme
            if ch["id"] in benzersiz:
                continue

            print(f"⏳ İşleniyor: {ch['name']}")
            captured_urls = []

            page = await context.new_page()

            def handle_request(request):
                url = request.url
                if ".m3u8" in url and "cloudflare" not in url and "beacon" not in url:
                    captured_urls.append(url)

            page.on("request", handle_request)

            try:
                await page.goto(ch["url"], wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(1500)

                m3u8 = None
                if captured_urls:
                    m3u8 = captured_urls[0]
                else:
                    # Sayfa içeriğinden dene
                    content = await page.content()
                    for m in re.finditer(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', content):
                        url = m.group(1)
                        if "cloudflare" not in url and "beacon" not in url:
                            m3u8 = url
                            break

                if m3u8:
                    tvg_id = normalize_tvg_id(ch["name"])
                    m3u.append(f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="Sell spor+sec izle",{ch["name"]}')
                    m3u.append(f"#EXTVLCOPT:http-referrer={referer}")
                    m3u.append(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}")
                    m3u.append(m3u8)
                    ok += 1
                    benzersiz.add(ch["id"])
                    print(f"🎯 M3U8 bulundu: {m3u8}")
                else:
                    print(f"❌ Link bulunamadı: {ch['name']}")
            except Exception as e:
                print(f"❌ Hata: {ch['name']} - {e}")
            finally:
                await page.close()

        await browser.close()

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))

    print(f"\n✅ M3U oluşturuldu: {filename}")
    print(f"📊 Başarılı: {ok}/{len(players)}")

if __name__ == "__main__":
    asyncio.run(create_m3u())
