import requests
import re
import sys
import os
import json

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"
COOKIES_FILE = "cookies.txt"

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
    except Exception as e:
        print(f"Cookie parse hatasi: {e}")
    return cookies

def get_live_video_id(channel_id, cookies):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    r = requests.get(url, headers=headers, cookies=cookies)
    match = re.search(r'"videoId":"([^"]{11})"', r.text)
    if match:
        return match.group(1)
    return None

def get_stream_url(video_id, cookies):
    clients = [
        {
            "name": "WEB",
            "clientName": "WEB",
            "clientVersion": "2.20240101.00.00",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "clientNameId": "1",
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
            "name": "TV_EMBEDDED",
            "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
            "clientVersion": "2.0",
            "userAgent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
            "clientNameId": "85",
        },
        {
            "name": "WEB_EMBEDDED",
            "clientName": "WEB_EMBEDDED_PLAYER",
            "clientVersion": "2.20240101.00.00",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "clientNameId": "56",
        },
    ]

    # Cookie string oluştur
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

    for client in clients:
        print(f"  Client deneniyor: {client['name']}...")
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
                json=payload,
                headers=headers,
                timeout=15
            )

            data = r.json()
            ps = data.get("playabilityStatus", {})
            print(f"    Status: {ps.get('status')} — {ps.get('reason', '')}")

            streaming = data.get("streamingData", {})

            hls = streaming.get("hlsManifestUrl")
            if hls:
                print(f"    HLS manifest bulundu!")
                return hls

            dash = streaming.get("dashManifestUrl")
            if dash:
                print(f"    DASH manifest bulundu!")
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

# Cookie oku
print("Cookie okunuyor...")
if not os.path.exists(COOKIES_FILE):
    print("Cookie dosyasi yok, bossz devam ediliyor...")
    cookies = {}
else:
    cookies = parse_cookies(COOKIES_FILE)
    print(f"{len(cookies)} cookie yuklendi.")

print("Video ID aliniyor...")
video_id = get_live_video_id(CHANNEL_ID, cookies)
if not video_id:
    print("Hata: Video ID bulunamadi")
    sys.exit(1)

print(f"Video ID: {video_id}")
print("Stream URL aliniyor...")

stream_url = get_stream_url(video_id, cookies)
if not stream_url:
    print("Hata: Stream URL bulunamadi")
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
