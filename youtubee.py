import requests
import re
import os
import urllib.parse
import urllib3
import time

# Uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
MAX_RETRIES = 5 # Kanal başına deneme
WAIT_TIME = 10

def update():
    try:
        print(f"Liste çekiliyor: {JSON_URL}")
        response = requests.get(JSON_URL, timeout=15)
        channels = response.json()
    except Exception as e:
        print(f"HATA: JSON listesi alınamadı: {e}")
        return

    for channel in channels:
        raw_name = channel.get("name", "Bilinmeyen_Kanal")
        # Dosya sistemine uygun isim temizliği
        clean_name = re.sub(r'[^\w\s-]', '', raw_name).strip().replace(" ", "_")
        live_url = channel.get("url", "").strip()
        
        if not live_url:
            continue

        print(f"\n>>> İşleniyor: {clean_name}")
        
        # Klasör oluşturma
        if not os.path.exists(clean_name):
            os.makedirs(clean_name)
            print(f"Klasör oluşturuldu: {clean_name}")

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 1. Aşama: Session/Cookie Al
                headers1 = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
                r1 = requests.get("https://ytdlp.online/", headers=headers1, verify=False, timeout=15)
                token = r1.cookies.get("session")

                if not token:
                    print(f"Deneme {attempt}: Session alınamadı.")
                    time.sleep(WAIT_TIME)
                    continue

                # 2. Aşama: Stream Linki Sorgula
                encoded_cmd = urllib.parse.quote(f"--get-url {live_url}")
                api_url = f"https://ytdlp.online/stream?command={encoded_cmd}"
                
                headers2 = {
                    "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                    "Cookie": f"session={token}",
                    "Referer": "https://ytdlp.online/"
                }
                
                r2 = requests.get(api_url, headers=headers2, verify=False, timeout=25)
                # Regex ile manifest linkini ayıkla
                match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', r2.text)

                if match:
                    final_link = match.group(1).strip()
                    m3u8_payload = (
                        "#EXTM3U\n"
                        "#EXT-X-VERSION:3\n"
                        "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
                        f"{final_link}"
                    )
                    
                    file_path = os.path.join(clean_name, f"{clean_name}.m3u8")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(m3u8_payload)
                    
                    print(f"BAŞARILI: {file_path} güncellendi.")
                    success = True
                    break
                else:
                    print(f"Deneme {attempt}: Manifest bulunamadı.")
            
            except Exception as e:
                print(f"Deneme {attempt} Hata: {e}")
            
            time.sleep(WAIT_TIME)

        if not success:
            print(f"!!! BAŞARISIZ: {clean_name} için link üretilemedi.")

if __name__ == "__main__":
    update()
