#!/usr/bin/env python3
"""
YouTube Canlı Yayın Güncelleyici (youtube2.txt Çıktılı)
- youtube.json'daki channel ID'lerini kullanır
- Her kanal için canlı yayın video ID'sini bulur
- youtube2.txt'ye embed URL formatında yazar
- Android uygulaması youtube2.txt'yi okur (kod değişmez)
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Sabitler ────────────────────────────────────────────
WORKSPACE = os.environ.get("GITHUB_WORKSPACE", ".")

# Girdi: channel ID listesi (JSON)
JSON_FILE = Path(WORKSPACE) / "youtube.json"

# Çıktı: Android'in okuduğu txt dosyası
OUTPUT_FILE = Path(WORKSPACE) / "youtube2.txt"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 15


def fetch_live_video_id(channel_id):
    """
    Kanalın /live sayfasından canlı yayın video ID'sini çeker.
    """
    url = f"https://www.youtube.com/channel/{channel_id}/live"

    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Cookie": "CONSENT=YES+cb",
    })

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            html = response.read().decode("utf-8", errors="ignore")

        patterns = [
            r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"',
            r'<meta property="og:url" content="https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"',
            r'"videoId":"([a-zA-Z0-9_-]{11})"',
            r'watch\?v=([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)

        return None
    except Exception as e:
        print(f"  ⚠️  Kanal hatası: {e}")
        return None


def main():
    print("=" * 70)
    print("📺 YouTube Canlı Yayın Güncelleyici → youtube2.txt")
    print("=" * 70)
    print(f"📁 Workspace: {WORKSPACE}")
    print(f"📄 Girdi (JSON): {JSON_FILE}")
    print(f"📄 Çıktı (TXT):  {OUTPUT_FILE}")
    print()

    # 1. JSON'u oku
    if not JSON_FILE.exists():
        print(f"❌ HATA: {JSON_FILE} bulunamadı!")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    channels = data.get("channels", [])
    print(f"📋 Toplam kanal: {len(channels)}\n")

    # 2. Her kanal için video ID bul
    video_urls = []
    success_count = 0

    for i, channel in enumerate(channels, 1):
        channel_id = channel.get("channelId", "")
        name = channel.get("name", "?")

        print(f"[{i}/{len(channels)}] {name}")
        print(f"  🔗 Channel ID: {channel_id}")

        if not channel_id:
            print(f"  ⏭️  Atlandı (Channel ID yok)")
            continue

        video_id = fetch_live_video_id(channel_id)

        if not video_id:
            print(f"  ❌ Canlı yayın bulunamadı")
            continue

        embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
        video_urls.append(embed_url)
        success_count += 1
        print(f"  ✅ {embed_url}")

    # 3. youtube2.txt'ye yaz (Android bunu okur)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in video_urls:
            f.write(f"{url}\n")

    # 4. JSON'a meta bilgileri de ekle (isteğe bağlı)
    data["success"] = True
    data["count"] = success_count
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["source"] = "github-actions"

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 70)
    print(f"✅ {success_count}/{len(channels)} kanal canlı yayında")
    print(f"💾 Kaydedildi: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
