import yt_dlp
import sys
import os
import subprocess

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"
COOKIES_FILE = "cookies.txt"

url = f"https://www.youtube.com/channel/{CHANNEL_ID}/live"

print("Yontem 1: ios client (cookie yok)...")
try:
    result = subprocess.run(
        [
            "yt-dlp",
            "--get-url",
            "--format", "best",
            "--extractor-args", "youtube:player_client=ios",
            url
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0 and result.stdout.strip():
        stream_url = result.stdout.strip().split('\n')[0]
        print(f"Basarili! URL: {stream_url[:80]}...")

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(
                "#EXTM3U\n"
                "#EXT-X-VERSION:3\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
                f"{stream_url}\n"
            )
        print(f"{OUTPUT_FILE} olusturuldu.")
        sys.exit(0)
    else:
        print(f"Basarisiz: {result.stderr[-300:]}")

except Exception as e:
    print(f"Hata: {e}")

print("Yontem 2: mweb client (cookie yok)...")
try:
    result = subprocess.run(
        [
            "yt-dlp",
            "--get-url",
            "--format", "best",
            "--extractor-args", "youtube:player_client=mweb",
            url
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode == 0 and result.stdout.strip():
        stream_url = result.stdout.strip().split('\n')[0]
        print(f"Basarili! URL: {stream_url[:80]}...")

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(
                "#EXTM3U\n"
                "#EXT-X-VERSION:3\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
                f"{stream_url}\n"
            )
        print(f"{OUTPUT_FILE} olusturuldu.")
        sys.exit(0)
    else:
        print(f"Basarisiz: {result.stderr[-300:]}")

except Exception as e:
    print(f"Hata: {e}")

print("Yontem 3: web client + cookie + node.js n challenge...")
if os.path.exists(COOKIES_FILE):
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--cookies", COOKIES_FILE,
                "--get-url",
                "--format", "best",
                "--extractor-args", "youtube:player_client=web",
                url
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "PATH": os.environ["PATH"]}
        )

        if result.returncode == 0 and result.stdout.strip():
            stream_url = result.stdout.strip().split('\n')[0]
            print(f"Basarili! URL: {stream_url[:80]}...")

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(
                    "#EXTM3U\n"
                    "#EXT-X-VERSION:3\n"
                    "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
                    f"{stream_url}\n"
                )
            print(f"{OUTPUT_FILE} olusturuldu.")
            sys.exit(0)
        else:
            print(f"Basarisiz: {result.stderr[-300:]}")

    except Exception as e:
        print(f"Hata: {e}")

print("Tum yontemler basarisiz.")
sys.exit(1)
