import re
import requests
from bs4 import BeautifulSoup

# Global ayarlar
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.selcuksportshd.is/"
}

def find_active_domain(start=680, end=750):
    """Sayısal olarak değişen aktif giriş domainini bulur."""
    print("🔍 Aktif domain taranıyor...")
    for i in range(start, end + 1):
        # Genellikle selcuksportshd + rastgele karakterler/sayılar + .xyz formatındadır
        # Örneğinizdeki 688829a7bd yapısı için geniş bir arama gerekebilir. 
        # Eğer statik bir listeniz varsa oradan devam edilebilir.
        url = f"https://www.selcuksportshd{i}.xyz/" 
        try:
            # Örnekte verdiğiniz tam URL'yi deniyoruz
            test_url = "https://www.selcuksportshd688829a7bd.xyz/"
            response = requests.get(test_url, headers=HEADERS, timeout=5)
            if response.status_code == 200 and "uxsyplayer" in response.text:
                return test_url, response.text
        except:
            continue
    return None, None

def get_m3u8_from_player(player_url, main_referer):
    """Player sayfasından baseStreamUrl'i çekip final m3u8 adresini oluşturur."""
    try:
        # Player sayfası için referer ana site olmalıdır
        res = requests.get(player_url, headers={"User-Agent": HEADERS["User-Agent"], "Referer": main_referer}, timeout=7)
        html = res.text

        # baseStreamUrl desenini ara
        pattern = r'this\.baseStreamUrl\s*=\s*["\']([^"\']+)["\']'
        match = re.search(pattern, html)
        
        if not match:
            return None

        base_url = match.group(1).rstrip('/') + '/'
        
        # ID parametresini URL'den çek (id=selcukbeinsports1 gibi)
        stream_id_match = re.search(r"id=([a-zA-Z0-9_-]+)", player_url)
        if not stream_id_match:
            return None
            
        stream_id = stream_id_match.group(1)
        return f"{base_url}{stream_id}/playlist.m3u8"

    except Exception as e:
        return None

def process_channels():
    domain, html = find_active_domain()
    if not domain:
        print("❌ Aktif kaynak bulunamadı.")
        return

    soup = BeautifulSoup(html, "html.parser")
    # Sadece futbol tabını (tab1) değil, tüm kanalları çekelim
    channel_links = soup.find_all("a", attrs={"data-url": True})
    
    print(f"📺 {len(channel_links)} kanal işleniyor...")
    
    m3u_content = ["#EXTM3U"]

    for a in channel_links:
        raw_url = a["data-url"]
        # 'gecersiz' olanları veya boş olanları atla
        if "gecersiz" in raw_url or not raw_url.startswith("http"):
            continue

        name_tag = a.find("div", class_="name")
        time_tag = a.find("time", class_="time")
        
        # Kanal adını temizle
        channel_name = name_tag.text.strip() if name_tag else "Bilinmeyen Kanal"
        if time_tag and time_tag.text.strip():
            channel_name = f"{channel_name} ({time_tag.text.strip()})"

        print(f"🔄 Bağlantı çözülüyor: {channel_name}")
        
        final_link = get_m3u8_from_player(raw_url, domain)
        
        if final_link:
            # ME TV için m3u formatı
            m3u_content.append(f'#EXTINF:-1, {channel_name}')
            # SelcukSports m3u8'leri Referer ve User-Agent kontrolü yapar, VLC/IPTV Player'da bunlar eklenmeli
            m3u_content.append(f'#EXTVLCOPT:http-referrer={domain}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(final_link)

    # Dosyaya kaydet
    with open("selcuk.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    print("\n✅ İşlem tamamlandı! 'me_tv_selcuk.m3u' dosyası oluşturuldu.")

if __name__ == "__main__":
    process_channels()
