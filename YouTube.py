import requests
import re
import sys
import json
import os
import urllib.parse
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"
COOKIES_FILE = "cookies.txt"

def get_video_id(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"}
    r = requests.get(url, headers=headers, timeout=15)
    match = re.search(r'"videoId":"([^"]{11})"', r.text)
    return match.group(1) if match else None

def parse_cookies(cookie_file):
    cookies = {}
    try:
        with open(cookie_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
    except:
        pass
    return cookies

# =====================
# YONTEM 1: ytdlp.online
# =====================
def yontem_ytdlp_online(channel_id, deneme_sayisi=5):
    print("Yontem 1: ytdlp.online deneniyor...")
    youtube_link = f"https://www.youtube.com/channel/{channel_id}/live"
    
    for attempt in range(1, deneme_sayisi + 1):
        print(f"  Deneme {attempt}/{deneme_sayisi}...")
        try:
            headers1 = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
            r1 = requests.get("https://ytdlp.online/", headers=headers1, verify=False, timeout=15)
            
            if "session" not in r1.cookies:
                print("  Session alinamadi.")
                time.sleep(10)
                continue
            
            token = r1.cookies.get("session")
            encoded = urllib.parse.quote(f"--get-url {youtube_link}")
            stream_url = f"https://ytdlp.online/stream?command={encoded}"
            
            headers2 = {
                "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                "Accept": "text/event-stream",
                "Referer": "https://ytdlp.online/",
                "Cookie": f"session={token}"
            }
            r2 = requests.get(stream_url, headers=headers2, verify=False, timeout=30)
            text = r2.text
            
            # manifest.googlevideo.com ara
            match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', text)
            if match:
                print("  manifest.googlevideo.com bulundu!")
                return match.group(1).strip()
            
            # Herhangi bir googlevideo URL ara
            match2 = re.search(r'data:\s*(https://[^\s]*googlevideo[^\s]+)', text)
            if match2:
                print("  googlevideo URL bulundu!")
                return match2.group(1).strip()
            
            print(f"  URL bulunamadi. Yanit: {text[:200]}")
            time.sleep(10)

        except Exception as e:
            print(f"  Hata: {e}")
            time.sleep(10)
    
    return None

# =====================
# YONTEM 2: InnerTube API + cookie
# =====================
def yontem_innertube(video_id, cookies):
    print("Yontem 2: InnerTube API deneniyor...")
    
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    clients = [
        {
            "name": "WEB",
            "clientName": "WEB",
            "clientVersion": "2.20240101.00.00",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "clientNameId": "1",
        },
        {
            "name": "TV_EMBEDDED",
            "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
            "clientVersion": "2.0",
            "userAgent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
            "clientNameId": "85",
        },
        {
            "name": "ANDROID_VR",
            "clientName": "ANDROID_VR",
            "clientVersion": "1.57.29",
            "androidSdkVersion": 30,
            "userAgent": "com.google.android.apps.youtube.vr.oculus/1.57.29 (Linux; U; Android 11)",
            "clientNameId": "28",
        },
        {
            "name": "WEB_EMBEDDED",
            "clientName": "WEB_EMBEDDED_PLAYER",
            "clientVersion": "2.20240101.00.00",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "clientNameId": "56",
        },
    ]

    for client in clients:
        print(f"  Client: {client['name']}...")
        try:
            payload = {
                "videoId": video_id,
                "context": {
                    "client": {
                        "clientName": client["clientName"],
                        "clientVersion": client["clientVersion"],
                        "hl": "tr",
                        "gl": "TR",
                        "utcOffsetMinutes": 180,
                    }
                }
            }
            if "androidSdkVersion" in client:
                payload["context"]["client"]["androidSdkVersion"] = client["androidSdkVersion"]

            headers = {
                "User-Agent": client["userAgent"],
                "Content-Type": "application/json",
                "X-YouTube-Client-Name": client["clientNameId"],
                "X-YouTube-Client-Version": client["clientVersion"],
                "Origin": "https://www.youtube.com",
                "Referer": "https://www.youtube.com/",
                "Cookie": cookie_str,
            }

            r = requests.post(
                "https://www.youtube.com/youtubei/v1/player",
                json=payload, headers=headers, timeout=15
            )
            data = r.json()
            ps = data.get("playabilityStatus", {})
            print(f"    Status: {ps.get('status')} — {ps.get('reason', '')}")

            streaming = data.get("streamingData", {})
            hls = streaming.get("hlsManifestUrl")
            if hls:
                print(f"    HLS bulundu!")
                return hls
            dash = streaming.get("dashManifestUrl")
            if dash:
                print(f"    DASH bulundu!")
                return dash
            formats = streaming.get("formats", []) + streaming.get("adaptiveFormats", [])
            for f in reversed(formats):
                u = f.get("url", "")
                if u:
                    print(f"    Direkt URL bulundu!")
                    return u

        except Exception as e:
            print(f"    Hata: {e}")

    return None

# =====================
# ANA AKIŞ
# =====================

# Cookie yükle
cookies = parse_cookies(COOKIES_FILE) if os.path.exists(COOKIES_FILE) else {}
print(f"{len(cookies)} cookie yuklendi.")

# Video ID al
print("Video ID aliniyor...")
video_id = get_video_id(CHANNEL_ID)
print(f"Video ID: {video_id}")

stream_url = None

# Yöntem 1: ytdlp.online
stream_url = yontem_ytdlp_online(CHANNEL_ID, deneme_sayisi=5)

# Yöntem 2: InnerTube API
if not stream_url and video_id:
    stream_url = yontem_innertube(video_id, cookies)

if not stream_url:
    print("Tum yontemler basarisiz.")
    sys.exit(1)

print(f"Basarili! URL: {stream_url[:80]}...")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
        f"{stream_url}\n"
    )

print(f"{OUTPUT_FILE} olusturuldu.")
