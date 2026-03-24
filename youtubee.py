import requests
import re
import os
import urllib.parse
import urllib3
import time
import json

# Uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
MAX_RETRIES = 10
WAIT_TIME = 15

def get_channels():
    try:
        print(f"Liste çekiliyor: {JSON_URL}")
        response = requests.get(JSON_URL, timeout=15)
        return response.json()
    except json.JSONDecodeError as e:
        print(f"KRİTİK HATA: JSON formatı bozuk! Satır: {e.lineno}, Sütun: {e.colno}")
        print("Lütfen JSON dosyasındaki yazım hatasını (fazladan virgül vb.) düzeltin.")
        return None
    except Exception as e:
        print(f"Liste alınamadı: {e}")
        return None

def main():
    channels = get_channels()
    if not channels:
        return

    for channel in channels:
        name = channel.get("name", "Bilinmeyen_Kanal").replace(" ", "_").replace("/", "-")
        target_url = channel.get("url", "").strip()

        if not target_url:
            continue

        print(f"\n--- {name} İşleniyor ---")
        
        # Klasör oluştur
        if not os.path.exists(name):
            os.makedirs(name)
            print(f"Klasör oluşturuldu: {name}")

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"Deneme {attempt}/{MAX_RETRIES}...")
            
            try:
                headers = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
                
                # 1. Oturum aç ve session al
                res1 = requests.get("https://ytdlp.online/", headers=headers, verify=False, timeout=15)
                token = res1.cookies.get("session")

                if not token:
                    print("Session alınamadı. Bekleniyor...")
                    time.sleep(WAIT_TIME)
                    continue

                # 2. Komutu hazırla ve stream linkini iste
                encoded_cmd = urllib.parse.quote(f"--get-url {target_url}")
                stream_api = f"https://ytdlp.online/stream?command={encoded_cmd}"
                
                headers["Cookie"] = f"session={token}"
                headers["Referer"] = "https://ytdlp.online/"
                headers["Accept"] = "text/event-stream"

                res2 = requests.get(stream_api, headers=headers, verify=False, timeout=25)
                
                # 3. Regex ile manifest linkini bul
                match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', res2.text)

                if match:
                    final_link = match.group(1).strip()
                    m3u8_content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{final_link}"

                    # Dosyayı klasörün içine kaydet
                    file_path = os.path.join(name, f"{name}.m3u8")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(m3u8_content)
                    
                    print(f"Başarılı! {name} için link kaydedildi.")
                    success = True
                    break
                else:
                    print("Manifest bulunamadı. Bekleniyor...")

            except Exception as e:
                print(f"Hata oluştu: {e}")
            
            if not success and attempt < MAX_RETRIES:
                time.sleep(WAIT_TIME)

        if not success:
            print(f"HATA: {name} için {MAX_RETRIES} deneme yapıldı ancak link bulunamadı.")

if __name__ == "__main__":
    main()
