import base64
import os
import re
import requests
import urllib3

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL Base64 ile şifrelendi (Kimse doğrudan düz metin olarak göremez)
ENCRYPTED_URL = "aHR0cHM6Ly95dHViZS13YXJzLm15d2lyZS5vcmcvbm91dHViZS9wbGF5bGlzdC5tM3U="

def create_coutubee_folder():
    if not os.path.exists("coutubee"):
        os.makedirs("coutubee")

def decrypt_url():
    decrypted_bytes = base64.b64decode(ENCRYPTED_URL)
    return decrypted_bytes.decode("utf-8", errors="ignore")

def fetch_playlist(url):
    response = requests.get(url, verify=False)
    response.raise_for_status()
    return response.content.decode("utf-8", errors="ignore")

def parse_playlist(content):
    lines = content.strip().split("\n")
    channels = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            match = re.search(r",(.+)$", lines[i])
            if match and i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                channel_name = match.group(1).strip()
                channel_url = lines[i + 1].strip()
                channels.append((channel_name, channel_url))
    return channels

def save_channel_as_m3u8(channel_name, stream_url):
    safe_name = "".join(c for c in channel_name if c.isalnum() or c in ".-_").rstrip()
    if not safe_name:
        safe_name = "channel"
    
    # Kanallar doğrudan coutubee klasörüne kaydedilir
    filename = f"coutubee/{safe_name}.m3u8"
    content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{stream_url}
"""
    with open(filename, "w", encoding="utf-8", errors="ignore") as f:
        f.write(content)
    print(f"Saved: {filename}")

def main():
    try:
        create_coutubee_folder()
        playlist_url = decrypt_url()
        print(f"Fetching playlist from: {playlist_url}")
        playlist_content = fetch_playlist(playlist_url)
        channels = parse_playlist(playlist_content)
        
        if not channels:
            print("No channels found in playlist.")
            return
        
        for name, url in channels:
            save_channel_as_m3u8(name, url)
        
        print(f"Successfully saved {len(channels)} channels.")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
