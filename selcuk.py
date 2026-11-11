import re
import requests
from bs4 import BeautifulSoup
import urllib3

# SSL uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
}

def find_active_domain():
    """Sitenin güncel çalışan domainini bulur."""
    # Güncel giriş adresleri buraya eklenebilir
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

def get_m3u8(iframe_url, referer):
    """
    Iframe URL'sine gidip içindeki JavaScript kodundan gerçek m3u8 linkini ayıklar.
    Örnek çıktı: https://dga1op10s1u3lea.aae77b66b9d557.click/live/selcukbeinsports1/playlist.m3u8
    """
    try:
        # Iframe sayfasına istek at
        res = requests.get(iframe_url, headers={**HEADERS, "Referer": referer}, timeout=10, verify=False)
        
        # 1. Yöntem: Eğer sayfa içinde doğrudan .m3u8 geçiyorsa
        match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', res.text)
        if match:
            return match.group(1)

        # 2. Yöntem: Player'ın kendi script yapısındaki değişkenleri ara
        # Örnek: this.baseStreamUrl = "https://..."; 
        base_url = re.search(r'this\.baseStreamUrl\s*=\s*["\']([^"\']+)["\']', res.text)
        
        # Kanal ID'sini URL'den çek (örn: id=selcukbeinsports1)
        channel_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', iframe_url)
        
        if base_url and channel_id_match:
            channel_id = channel_id_match.group(1)
            # Linki birleştir (Sondaki / işaretini temizleyerek)
            return f"{base_url.group(1).rstrip('/')}/{channel_id}/playlist.m3u8"
            
    except Exception as e:
        print(f"  [Hata: {e}]")
    return None

def run():
    domain, html = find_active_domain()
    if not domain:
        print("[-] Aktif domain bulunamadı.")
        return
    
    soup = BeautifulSoup(html, "html.parser")
    # Sayfadaki tüm data-url barındıran (kanal) a etiketlerini bul
    items = soup.find_all("a", attrs={"data-url": True})
    
    m3u_lines = ["#EXTM3U"]
    basarili = 0
    
    print(f"[*] Toplam {len(items)} kanal bulundu. Test ediliyor...\n")

    for item in items:
        raw_url = item["data-url"]
        
        # Geçersiz kanalları atla
        if "gecersiz" in raw_url or not raw_url.startswith("http") or "Undefined" in raw_url: 
            continue
        
        # Kanal ismini çek
        name_div = item.find("div", class_="name")
        name = name_div.get_text(strip=True) if name_div else "Bilinmeyen Kanal"
        
        # Iframe içinden m3u8 linkini al
        link = get_m3u8(raw_url, domain)
        
        if link:
            print(f"[✓] {name} -> {link}")
            m3u_lines.append(f'#EXTINF:-1, {name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={domain}')
            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_lines.append(link)
            basarili += 1
        else:
            print(f"[✗] {name} (Link bulunamadı)")

    # M3U dosyasını kaydet
    with open("selcuksports.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
        
    print(f"\n[İşlem Tamamlandı] {basarili} kanal başarıyla eklendi. Dosya: selcuksports.m3u")

if __name__ == "__main__":
    run()
