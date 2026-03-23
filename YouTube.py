import subprocess
import sys
import os

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"
COOKIES_FILE = "cookies.txt"

url = f"https://www.youtube.com/channel/{CHANNEL_ID}/live"

# node path'i bul ve yt-dlp'ye bildir
node_path = subprocess.run(["which", "node"], capture_output=True, text=True).stdout.strip()
print(f"Node path: {node_path}")

env = os.environ.copy()
if node_path:
    env["PATH"] = os.path.dirname(node_path) + ":" + env.get("PATH", "")

DENE = [
    ["--extractor-args", "youtube:player_client=web", "--cookies", COOKIES_FILE],
    ["--extractor-args", "youtube:player_client=web_creator", "--cookies", COOKIES_FILE],
    ["--extractor-args", "youtube:player_client=android_vr"],
    ["--extractor-args", "youtube:player_client=android_testsuite"],
    ["--extractor-args", "youtube:player_client=android_producer"],
]

for args in DENE:
    label = " ".join(args[:2])
    print(f"Deneniyor: {label}...")
    try:
        cmd = ["yt-dlp", "--get-url", "--format", "best"] + args + [url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)

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
            hata = result.stderr.strip().split('\n')[-1]
            print(f"  Basarisiz: {hata[-150:]}")

    except subprocess.TimeoutExpired:
        print(f"  Zaman asimi.")
    except Exception as e:
        print(f"  Hata: {e}")

print("Tum yontemler basarisiz.")
sys.exit(1)
