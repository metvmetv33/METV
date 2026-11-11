import re
import requests
import base64
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
}

def find_active_domain():
    """Sitenin güncel çalışan domainini bulur."""
    test_urls = [
        "https://www.selcuksportshd14e17ba2ad.xyz/", 
        "https://www.selcuksportshd.is/",
        "https://www.selcuksportshd0.xyz/"
    ]
    for url in test_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "data-url" in res.text:
                print(f"[+] Aktif Domain Bulundu: {url}")
                return url, res.text
        except:
            continue
    return None, None

def get_m3u8(iframe_url, referer, channel_id):
    """
    Iframe URL'sine gidip içindeki JavaScript kodundan gerçek m3u8 linkini ayıklar.
    Hedef format: https://dga1op10s1u3lea.aae77b66b9d557.click/live/selcukbeinsports1/playlist.m3u8
    """
    try:
        res = requests.get(iframe_url, headers={**HEADERS, "Referer": referer}, timeout=10, verify=False)
        html = res.text

        # 1. Yöntem: Doğrudan .m3u8 linki var mı? (Cloudflare analiz scriptlerini filtrele)
        for m in re.finditer(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', html):
            url = m.group(1)
            if 'cloudflareinsights' not in url and 'beacon.min.js' not in url:
                return url

        # 2. Yöntem: Base64 ile şifrelenmiş link var mı?
        b64_matches = re.findall(r'atob\([\'"]([^\'"]+)[\'"]\)', html)
        for b64 in b64_matches:
            try:
                decoded = base64.b64decode(b64).decode('utf-8')
                for m in re.finditer(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', decoded):
                    url = m.group(1)
                    if 'cloudflareinsights' not in url and 'beacon.min.js' not in url:
                        return url
            except:
                pass

        # 3. Yöntem: Iframe içindeki .click uzantılı domainleri bul (Cloudflare hariç)
        # Örnek: https://dga1op10s1u3lea.aae77b66b9d557.click
        click_domains = re.findall(r'["\'\(](https?://([a-z0-9]+\.)?[a-z0-9]+\.click)(?:[/"\')])', html, re.IGNORECASE)
        
        adaylar = []
        for full, _ in click_domains:
            if 'cloudflare' in full.lower():
                continue
            adaylar.append(full.rstrip('/'))

        # Benzersiz yap ve uzun olanları (rastgele hex içerenleri) öne al
        benzersiz = sorted(set(adaylar), key=len, reverse=True)

        for base in benzersiz:
            candidate = f"{base}/live/{channel_id}/playlist.m3u8"
            # Linkin gerçekten var olup olmadığını test et
            try:
                test = requests.head(candidate, headers=HEADERS, timeout=5, verify=False, allow_redirects=True)
                if test.status_code in (200, 206):
                    return candidate
            except:
                pass

        # Test başarısız olsa bile en olası adayı döndür (çoğu zaman çalışır)
        if benzersiz:
            return f"{benzersiz[0]}/live/{channel_id}/playlist.m3u8"

    except Exception as e:
        pass
    return None

def run():
    domain, html = find_active_domain()
    if not domain:
        print("[-] Aktif domain bulunamadı.")
        return
    
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("a", attrs={"data-url": True})
    
    m3u_lines = ["#EXTM3U"]
    basarili = 0
    
    print(f"[*] Toplam {len(items)} kanal bulundu. Test ediliyor...\n")

    for item in items:
        raw_url = item["data-url"]
        
        if "gecersiz" in raw_url or not raw_url.startswith("http") or "Undefined" in raw_url: 
            continue
        
        name_div = item.find("div", class_="name")
        name = name_div.get_text(strip=True) if name_div else "Bilinmeyen Kanal"
        
        # Kanal ID'sini iframe URL'sinden çek (örn: id=selcukbeinsports1)
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)', raw_url)
        channel_id = id_match.group(1) if id_match else None
        
        if channel_id:
            link = get_m3u8(raw_url, domain, channel_id)
        else:
            link = None
        
        if link:
            print(f"[✓] {name} -> {link}")
            m3u_lines.append(f'#EXTINF:-1, {name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={domain}')
            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_lines.append(link)
            basarili += 1
        else:
            print(f"[✗] {name} (Link bulunamadı)")

    with open("selcuksports.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
        
    print(f"\n[İşlem Tamamlandı] {basarili} kanal başarıyla eklendi. Dosya: selcuksports.m3u")

if __name__ == "__main__":
    run()
