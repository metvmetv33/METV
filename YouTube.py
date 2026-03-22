import subprocess
import sys
import os

def install_ytdlp():
    subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"], check=True)

def get_manifest(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    
    result = subprocess.run([
        "yt-dlp",
        "--get-url",
        "-f", "best",
        "--no-warnings",
        url
    ], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip().split("\n")[0]
    
    print(f"Hata: {result.stderr[:200]}")
    return None

# Kur
install_ytdlp()

CHANNELS = {
    "UC9TDTjbOjFB9jADmPhSAPsw": "kanal1",
    "UCoIUysIrvGxoDw-GkdOGjRw": "kanal2",
}

results = {}
for channel_id, name in CHANNELS.items():
    print(f"[{name}] işleniyor...")
    url = get_manifest(channel_id)
    if url:
        results[name] = url
        print(f"[{name}] Başarılı: {url[:60]}...")
    else:
        print(f"[{name}] BULUNAMADI")

with open("manifest.txt", "w") as f:
    for name, url in results.items():
        f.write(f"{name}={url}\n")

print("manifest.txt güncellendi.")
