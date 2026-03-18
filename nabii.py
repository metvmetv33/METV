import os
import shutil
import requests
import re

# Tüm Tabii kanallarını içeren genişletilmiş sözlük
source_urls = {
    "trt1": "https://www.tabii.com/tr/watch/live/trt1?trackId=150002",
    "trt2": "https://www.tabii.com/tr/watch/live/trt2?trackId=150007",
    "trtspor": "https://www.tabii.com/tr/watch/live/trtspor?trackId=150022",
    "trthaber": "https://www.tabii.com/tr/watch/live/trthaber?trackId=150017",
    "trtsporyildiz": "https://www.tabii.com/tr/watch/live/trtsporyildiz?trackId=150028",
    "trtcocuk": "https://www.tabii.com/tr/watch/live/trtcocuk?trackId=150038",
    "trtworld": "https://www.tabii.com/tr/watch/live/trtworld?trackId=150063",
    "trtbelgesel": "https://www.tabii.com/tr/watch/live/trtbelgesel?trackId=150012",
    "trtmuzik": "https://www.tabii.com/tr/watch/live/trtmuzik?trackId=150033",
    "trtturk": "https://www.tabii.com/tr/watch/live/trtturk?trackId=150043",
    "trtkurdi": "https://www.tabii.com/tr/watch/live/trtkurdi?trackId=150053",
    "trtarabi": "https://www.tabii.com/tr/watch/live/trtarabi?trackId=150058",
    "trtavaz": "https://www.tabii.com/tr/watch/live/trtavaz?trackId=150048",
    "trtgenc": "https://www.tabii.com/tr/watch/live/trtgenc?trackId=606324",
    "trteba": "https://www.tabii.com/tr/watch/live/trteba?trackId=293389",
    "trtdiyanetcocuk": "https://www.tabii.com/tr/watch/live/trtdiyanetcocuk?trackId=171018",
    "tabiispor": "https://www.tabii.com/tr/watch/live/tabiispor?trackId=419561",
    "tabiispor1": "https://www.tabii.com/tr/watch/live/tabiispor1?trackId=401207",
    "tabiispor2": "https://www.tabii.com/tr/watch/live/tabiispor2?trackId=404583",
    "tabiispor3": "https://www.tabii.com/tr/watch/live/tabiispor3?trackId=404630",
    "tabiispor4": "https://www.tabii.com/tr/watch/live/tabiispor4?trackId=404637",
    "tabiispor5": "https://www.tabii.com/tr/watch/live/tabiispor5?trackId=404646",
    "tabiispor6": "https://www.tabii.com/tr/watch/live/tabiispor6?trackId=404666",
    "tabiitv": "https://www.tabii.com/tr/watch/live/tabiitv?trackId=383911",
    "tabiicocuk": "https://www.tabii.com/tr/watch/live/tabii-cocuk?trackId=516992"
}

stream_folder = "stream"

# Klasör yönetimi
if os.path.exists(stream_folder):
    shutil.rmtree(stream_folder)
os.makedirs(stream_folder)

def extract_m3u8(url):
    """Web sayfasından .m3u8 linkini çekmeye çalışır."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.tabii.com/'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        text = response.text

        # Hem standart hem de kaçış karakterli (backslash) m3u8 linklerini yakalar
        matches = re.findall(r'https?[:\\/]+[^\s\'"]+\.m3u8[^\s\'"]*', text)
        
        if matches:
            # Kaçış karakterlerini temizle (\/ -> /)
            clean_url = matches[0].replace('\\/', '/')
            return clean_url
        return None
    except Exception as e:
        print(f"[HATA] {url} -> {e}")
        return None

def write_multi_variant_m3u8(filename, url):
    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        f"#EXT-X-STREAM-INF:BANDWIDTH=1500000,RESOLUTION=1920x1080\n"
        f"{url}\n"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    for name, page_url in source_urls.items():
        print(f"[+] {name} işleniyor...")
        m3u8_link = extract_m3u8(page_url)
        
        if m3u8_link:
            file_path = os.path.join(stream_folder, f"{name}.m3u8")
            write_multi_variant_m3u8(file_path, m3u8_link)
            print(f"[✓] {name}.m3u8 oluşturuldu.")
        else:
            print(f"[X] {name} için link bulunamadı.")

print("\n[*] İşlem tamamlandı.")
