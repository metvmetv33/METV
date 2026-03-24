import requests
import re
import os
import urllib.parse
import urllib3
import time
import json

# Güvenlik uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
MAX_RETRIES = 5
WAIT_TIME = 10

def get_channels():
    try:
        print(f"Liste çekiliyor: {JSON_URL}")
        response = requests.get(JSON_URL, timeout=20)
        # JSON bozuksa bile manuel temizlik deneyen esnek yükleme
        text = response.text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Eğer sonunda virgül kaldıysa onu temizlemeye çalışır
            print("JSON bozuk görünüyor, tamir edilmeye çalışılıyor...")
            fixed_text = re.sub(r',\s*\]', ']', text) 
            return json.loads(fixed_text)
    except Exception as e:
        print(f"Liste okuma hatası: {e}")
        return None

def main():
    channels = get_channels()
    if not channels:
        print("Kanal listesi boş veya alınamadı.")
        return

    for channel in channels:
        # Kanal ismi ve URL temizliği
        raw_name = channel.get("name", "Bilinmeyen")
        clean_name = re.sub(r'[^\w\s-]', '', raw_name).strip().replace(" ", "_")
        target_url = channel.get("url", "").strip()

        if not target_url:
            continue

        print(f"\n--- İşleniyor: {clean_name} ---")
        
        # Klasör oluşturma (Örn: CNN_TÜRK/)
        if not os.path.exists(clean_name):
            os.makedirs(clean_name)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # 1. Aşama: Oturum/Token Al
                headers = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
                res1 = requests.get("https://ytdlp.online/", headers=headers, verify=False, timeout=15)
                token = res1.cookies.get("session")

                if not token:
                    time.sleep(WAIT_TIME)
                    continue

                # 2. Aşama: Stream Linki Al
                encoded_cmd = urllib.parse.quote(f"--get-url {target_url}")
                stream_api = f"https://ytdlp.online/stream?command={encoded_cmd}"
                
                headers.update({
                    "Cookie": f"session={token}",
                    "Referer": "https://ytdlp.online/",
                    "Accept": "text/event-stream"
                })

                res2 = requests.get(stream_api, headers=headers, verify=False, timeout=25)
                match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', res2.text)

                if match:
                    final_link = match.group(1).strip()
                    m3u8_payload = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{final_link}"

                    # Klasörün içine dosyayı yaz (Örn: CNN_TÜRK/CNN_TÜRK.m3u8)
                    file_path = os.path.join(clean_name, f"{clean_name}.m3u8")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(m3u8_payload)
                    
                    print(f"BAŞARILI: {file_path}")
                    success = True
                    break
                else:
                    print(f"Deneme {attempt}: Link bulunamadı.")
            except Exception as e:
                print(f"Deneme {attempt} Hata: {e}")
            
            time.sleep(WAIT_TIME)

if __name__ == "__main__":
    main()
