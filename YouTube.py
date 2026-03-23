import requests
import re
import sys
import json

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"

def get_live_video_id(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    r = requests.get(url, headers=headers)
    match = re.search(r'"videoId":"([^"]{11})"', r.text)
    if match:
        return match.group(1)
    return None

def get_stream_url(video_id):
    clients = [
        {
            "name": "ANDROID_TESTSUITE",
            "clientName": "ANDROID_TESTSUITE",
            "clientVersion": "1.9",
            "androidSdkVersion": 30,
            "userAgent": "com.google.android.youtube/1.9 (Linux; U; Android 11)",
            "apiKey": "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w",
            "clientNameId": "30",
        },
        {
            "name": "ANDROID_VR",
            "clientName": "ANDROID_VR",
            "clientVersion": "1.57.29",
            "androidSdkVersion": 30,
            "userAgent": "com.google.android.apps.youtube.vr.oculus/1.57.29 (Linux; U; Android 11)",
            "apiKey": "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w",
            "clientNameId": "28",
        },
        {
            "name": "IOS",
            "clientName": "IOS",
            "clientVersion": "19.29.1",
            "deviceModel": "iPhone16,2",
            "userAgent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)",
            "apiKey": "AIzaSyB-63vPrdThhKuerbB2N_l7Kvxy3HjsOXU",
            "clientNameId": "5",
        },
    ]

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
            if "deviceModel" in client:
                payload["context"]["client"]["deviceModel"] = client["deviceModel"]

            headers = {
                "User-Agent": client["userAgent"],
                "Content-Type": "application/json",
                "X-YouTube-Client-Name": client["clientNameId"],
                "X-YouTube-Client-Version": client["clientVersion"],
                "Origin": "https://www.youtube.com",
            }

            r = requests.post(
                f"https://www.youtube.com/youtubei/v1/player?key={client['apiKey']}",
                json=payload,
                headers=headers,
                timeout=15
            )

            data = r.json()

            # Debug: playabilityStatus
            ps = data.get("playabilityStatus", {})
            print(f"    playabilityStatus: {ps.get('status')} — {ps.get('reason', '')}")

            streaming = data.get("streamingData", {})

            # HLS manifest (canlı yayın için en iyi)
            hls = streaming.get("hlsManifestUrl")
            if hls:
                print(f"    HLS manifest bulundu!")
                return hls

            # DASH manifest
            dash = streaming.get("dashManifestUrl")
            if dash:
                print(f"    DASH manifest bulundu!")
                return dash

            # Direkt URL
            formats = streaming.get("formats", []) + streaming.get("adaptiveFormats", [])
            for f in reversed(formats):
                u = f.get("url", "")
                if u:
                    print(f"    Direkt URL bulundu!")
                    return u

            print(f"    streamingData: {list(streaming.keys())}")

        except Exception as e:
            print(f"    Hata: {e}")

    return None

print("Video ID aliniyor...")
video_id = get_live_video_id(CHANNEL_ID)
if not video_id:
    print("Hata: Video ID bulunamadi")
    sys.exit(1)

print(f"Video ID: {video_id}")
print("Stream URL aliniyor...")

stream_url = get_stream_url(video_id)
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
