import re
import asyncio
import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
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
            if res.status_code == 200 and "data-url" in res.text:
                print(f"[+] Aktif Domain: {url}")
                return url, res.text
        except:
            continue
    return None, None

async def main():
    domain, html = find_active_domain()
    if not domain:
        print("[-] Domain bulunamadı.")
        return

    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("a", attrs={"data-url": True})

    m3u_lines = ["#EXTM3U"]
    basarili = 0
    benzersiz_kanallar = set() # Aynı kanalı tekrar denememek için

    print(f"[*] Toplam {len(items)} kanal bulundu. Hızlandırılmış modda test ediliyor...\n")

    # Tek bir tarayıcı açıyoruz
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])

        for item in items:
            raw_url = item["data-url"]
            
            # Geçersizleri atla
            if "gecersiz" in raw_url or not raw_url.startswith("http") or "Undefined" in raw_url: 
                continue

            # Kanal ID'sini çek
            id_match = re.search(r'id=([a-zA-Z0-9_-]+)', raw_url)
            if not id_match:
                continue
            channel_id = id_match.group(1)

            # Aynı kanal ID'si daha önce eklendiyse atla (örneğin Tivibu Spor 1 ve Tivibu Spor aynı ID'ye sahip olabilir)
            if channel_id in benzersiz_kanallar:
                continue

            name_div = item.find("div", class_="name")
            name = name_div.get_text(strip=True) if name_div else "Bilinmeyen"

            # Her kanal için yeni bir sekme açıyoruz
            page = await context.new_page()
            captured_urls = []

            # Ağ isteklerini dinle
            def handle_request(request):
                url = request.url
                if ".m3u8" in url and "cloudflare" not in url and "beacon" not in url:
                    captured_urls.append(url)

            page.on("request", handle_request)

            try:
                # Sayfaya git ve ağın durulmasını bekle (timeout süresini kısa tuttuk)
                await page.goto(raw_url, wait_until="networkidle", timeout=15000)
                # Video oynatıcının m3u8 isteğini atması için çok kısa bir süre bekle
                await page.wait_for_timeout(1500) 

                if captured_urls:
                    link = captured_urls[0]
                    print(f"[✓] {name} -> {link}")
                    m3u_lines.append(f'#EXTINF:-1, {name}')
                    m3u_lines.append(f'#EXTVLCOPT:http-referrer={domain}')
                    m3u_lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_lines.append(link)
                    basarili += 1
                    benzersiz_kanallar.add(channel_id)
                else:
                    print(f"[✗] {name} (Link bulunamadı)")
            except Exception as e:
                print(f"[✗] {name} (Zaman aşımı veya hata)")
            finally:
                await page.close() # Sekmeyi kapat, tarayıcıyı açık tut

        await browser.close()

    # Çıktıyı kaydet
    with open("selcuksports.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"\n[✓] {basarili} kanal kaydedildi. Dosya: selcuksports.m3u")

if __name__ == "__main__":
    asyncio.run(main())
