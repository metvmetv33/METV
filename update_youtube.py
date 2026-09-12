#!/usr/bin/env python3
"""
YouTube Video Listesi Güncelleyici → youtube2.txt

Ne yapar?
1. youtube.json'dan kanal ID'lerini okur (canlı yayınlar)
2. youtube_videos.txt'den sabit video ID'lerini okur (normal videolar)
3. İkisini birleştirip youtube2.txt'ye yazar

Çıktı: youtube2.txt (Android bunu okur)
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Sabitler ────────────────────────────────────────────
WORKSPACE = os.environ.get("GITHUB_WORKSPACE", ".")

# Girdi dosyaları
JSON_FILE = Path(WORKSPACE) / "youtube.json"           # Canlı yayın kanalları
VIDEOS_FILE = Path(WORKSPACE) / "youtube_videos.txt"   # Sabit videolar

# Çıktı
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
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"  ⚠️  {e}")
        return None


def main():
    print("=" * 70)
    print("📺 YouTube Video Listesi Güncelleyici → youtube2.txt")
    print("=" * 70)
    print(f"📁 Workspace: {WORKSPACE}")
    print(f"📄 JSON (canlı): {JSON_FILE} (var: {JSON_FILE.exists()})")
    print(f"📄 TXT (sabit): {VIDEOS_FILE} (var: {VIDEOS_FILE.exists()})")
    print(f"📄 Çıktı: {OUTPUT_FILE}")
    print()

    embed_urls = []
    live_count = 0
    fixed_count = 0

    # ── 1. Canlı yayınlar (youtube.json)
    if JSON_FILE.exists():
        print("📡 Canlı yayınlar okunuyor...")
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        channels = data.get("channels", [])
        print(f"  📋 {len(channels)} kanal\n")

        for i, channel in enumerate(channels, 1):
            channel_id = channel.get("channelId", "")
            name = channel.get("name", "?")

            print(f"[Canlı {i}/{len(channels)}] {name}")

            if not channel_id:
                print(f"  ⏭️  Atlandı")
                continue

            video_id = fetch_live_video_id(channel_id)

            if video_id:
                embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
                embed_urls.append(embed_url)
                live_count += 1
                print(f"  ✅ {embed_url}")
            else:
                print(f"  ❌ Canlı yayın bulunamadı")
    else:
        print(f"⚠️  {JSON_FILE} bulunamadı, canlı yayınlar atlanıyor")

    print()

    # ── 2. Sabit videolar (youtube_videos.txt)
    if VIDEOS_FILE.exists():
        print("📡 Sabit videolar okunuyor...")
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            video_ids = [
                line.strip() for line in f
                if line.strip() and not line.startswith("#")
            ]

        print(f"  📋 {len(video_ids)} video ID\n")

        for i, video_id in enumerate(video_ids, 1):
            # Zaten embed URL mi kontrol et
            if video_id.startswith("http"):
                if "/embed/" in video_id:
                    video_id = video_id.split("/embed/")[-1].split("?")[0].strip()
                else:
                    continue

            embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"

            # Tekrar kontrolü
            if embed_url not in embed_urls:
                embed_urls.append(embed_url)
                fixed_count += 1
                print(f"  ✅ [{i}] {embed_url}")
            else:
                print(f"  ⏭️  [{i}] Tekrar, atlandı: {video_id}")
    else:
        print(f"⚠️  {VIDEOS_FILE} bulunamadı, sabit videolar atlanıyor")

    # ── 3. youtube2.txt'ye yaz
    print()
    print(f"💾 {len(embed_urls)} URL youtube2.txt'ye yazılıyor...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in embed_urls:
            f.write(f"{url}\n")

    print()
    print("=" * 70)
    print(f"✅ Canlı yayınlar: {live_count}")
    print(f"✅ Sabit videolar: {fixed_count}")
    print(f"📊 TOPLAM: {len(embed_urls)}")
    print(f"💾 Kaydedildi: {OUTPUT_FILE}")
    print(f"📅 Tarih: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
