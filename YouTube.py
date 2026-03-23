import requests
import re
import sys
import json
import os
import urllib.parse
import urllib3
import time
import hashlib
import base64

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    except:
        pass
    return cookies

def get_video_id(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"}
    r = requests.get(url, headers=headers, timeout=15)
    match = re.search(r'"videoId":"([^"]{11})"', r.text)
    return match.group(1) if match else None

def get_visitor_data(cookies):
    """YouTube'dan visitor_data al"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }
        r = requests.get("https://www.youtube.com", headers=headers, cookies=cookies, timeout=15)
        match = re.search(r'"visitorData":"([^"]+)"', r.text)
        if match:
            return match.group(1)
    except:
        pass
    return None

def yontem_innertube_visitor(video_id, cookies):
    print("Yontem: InnerTube + visitorData...")
    
    visitor_data = get_visitor_data(cookies)
    print(f"  visitorData: {visitor_data[:30] if visitor_data else 'Alinamadi'}...")
    
    cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    clients = [
        {
            "name": "WEB",
            "clientName": "WEB",
            "clientVersion": "2.20240724.00.00",
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
            "name": "WEB_CREATOR",
            "clientName": "WEB_CREATOR",
            "clientVersion": "1.20240724.03.00",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "clientNameId": "62",
        },
    ]

    for client in clients:
        print(f"  Client: {client['name']}...")
        try:
            client_ctx = {
                "clientName": client["clientName"],
                "clientVersion": client["clientVersion"],
                "hl": "tr",
                "gl": "TR",
                "utcOffsetMinutes": 180,
            }
            if visitor_data:
                client_ctx["visitorData"] = visitor_data
            if "androidSdkVersion" in client:
                client_ctx["androidSdkVersion"] = client["androidSdkVersion"]

            payload = {
                "videoId": video_id,
                "context": {
                    "client": client_ctx,
                    "user": {"lockedSafetyMode": False},
                    "request": {"useSsl": True},
                }
            }

            headers = {
                "User-Agent": client["userAgent"],
                "Content-Type": "application/json",
                "X-YouTube-Client-Name": client["clientNameId"],
                "X-YouTube-Client-Version": client["clientVersion"],
                "X-Origin": "https://www.youtube.com",
                "Origin": "https://www.youtube.com",
                "Referer": f"https://www.youtube.com/watch?v={video_id}",
                "Cookie": cookie_str,
                "Accept-Language": "tr-TR,tr;q=0.9",
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

def yontem_ytdlp_online(channel_id):
    """ytdlp.online — farklı endpoint dene"""
    print("Yontem: ytdlp.online (alternatif komut)...")
    youtube_link = f"https://www.youtube.com/channel/{channel_id}/live"
    
    for attempt in range(1, 4):
        print(f"  Deneme {attempt}/3...")
        try:
            headers1 = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
            r1 = requests.get("https://ytdlp.online/", headers=headers1, verify=False, timeout=15)
            
            if "session" not in r1.cookies:
                print("  Session alinamadi.")
                time.sleep(15)
                continue
            
            token = r1.cookies.get("session")
            
            # --get-url yerine farklı format dene
            cmd = f"--get-url --format best {youtube_link}"
            encoded = urllib.parse.quote(cmd)
            
            headers2 = {
                "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                "Accept": "text/event-stream",
                "Referer": "https://ytdlp.online/",
                "Cookie": f"session={token}"
            }
            r2 = requests.get(
                f"https://ytdlp.online/stream?command={encoded}",
                headers=headers2, verify=False, timeout=60
            )
            text = r2.text
            print(f"  Tam yanit:\n{text[:500]}")
            
            for pattern in [
                r'data:\s*(https://manifest\.googlevideo\.com[^\s<]+)',
                r'data:\s*(https://[^\s<]*googlevideo[^\s<]+)',
                r'(https://manifest\.googlevideo\.com[^\s<"]+)',
            ]:
                match = re.search(pattern, text)
                if match:
                    url = match.group(1).strip()
                    print(f"  URL bulundu!")
                    return url
            
            time.sleep(15)

        except Exception as e:
            print(f"  Hata: {e}")
            time.sleep(15)
    
    return None

# Ana akış
cookies = parse_cookies(COOKIES_FILE) if os.path.exists(COOKIES_FILE) else {}
print(f"{len(cookies)} cookie yuklendi.")

video_id = get_video_id(CHANNEL_ID)
print(f"Video ID: {video_id}")

stream_url = yontem_ytdlp_online(CHANNEL_ID)

if not stream_url and video_id:
    stream_url = yontem_innertube_visitor(video_id, cookies)

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
