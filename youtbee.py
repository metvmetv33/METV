import subprocess
import requests
import re
import os
import json
import time
from typing import Optional

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL      = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
OUTPUT_FOLDER = "metv2"
MAX_RETRIES   = 3
WAIT_TIME     = 5
COOKIES_FROM_BROWSER = None  # "chrome" / "firefox" / "edge" — GitHub Actions'ta None bırak
# ───────────────────────────────────────────────────────────


def get_channels():
    """JSON kanal listesini GitHub'dan çek."""
    print(f"[*] Kanal listesi çekiliyor: {JSON_URL}")
    try:
        r = requests.get(JSON_URL, timeout=20)
        r.raise_for_status()
        data = r.json()
        print(f"[+] {len(data)} kanal bulundu.")
        return data
    except Exception as e:
        print(f"[!] Liste alınamadı: {e}")
        return []


def get_stream_url(channel_url):
    # type: (str) -> Optional[str]
    """
    yt-dlp ile canlı yayının doğrudan stream URL'sini al.
    Başarısız olursa None döner.
    """
    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "--no-warnings",
        "-f", "best",
        "-g",
        "--no-playlist",
    ]

    if COOKIES_FROM_BROWSER:
        cmd += ["--cookies-from-browser", COOKIES_FROM_BROWSER]

    cmd.append(channel_url)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout.strip()
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("http"):
                    return line

            err_lines = result.stderr.strip().splitlines()
            hint = next((l for l in err_lines if "ERROR" in l or "WARNING" in l), "")
            print(f"    Deneme {attempt}/{MAX_RETRIES}: URL bulunamadı. {hint[:120]}")

        except subprocess.TimeoutExpired:
            print(f"    Deneme {attempt}/{MAX_RETRIES}: Zaman aşımı.")
        except FileNotFoundError:
            print("[!] 'yt-dlp' bulunamadı! Kurun: pip install yt-dlp")
            return None
        except Exception as e:
            print(f"    Deneme {attempt}/{MAX_RETRIES}: Hata — {e}")

        if attempt < MAX_RETRIES:
            print(f"    {WAIT_TIME}s bekleniyor...")
            time.sleep(WAIT_TIME)

    return None


def sanitize(name):
    # type: (str) -> str
    """Dosya adı için geçersiz karakterleri temizle."""
    return re.sub(r'[^\w\s\-]', '', name).strip().replace(" ", "_")


def save_m3u8(file_path, stream_url, channel_name):
    # type: (str, str, str) -> None
    """Tek kanallık .m3u8 dosyası oluştur."""
    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        f"#EXTINF:-1 tvg-name=\"{channel_name}\",{channel_name}\n"
        f"{stream_url}\n"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    channels = get_channels()
    if not channels:
        print("[!] Kanal listesi boş, çıkılıyor.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"[*] Dosyalar '{OUTPUT_FOLDER}/' klasörüne kaydedilecek.\n")

    success_count = 0
    fail_count    = 0
    failed_names  = []

    for i, ch in enumerate(channels, 1):
        name       = ch.get("name", f"Kanal_{i}")
        target_url = ch.get("url", "").strip()

        if not target_url:
            print(f"[{i}/{len(channels)}] '{name}': URL yok, atlanıyor.")
            continue

        print(f"[{i}/{len(channels)}] {name}")
        print(f"    URL: {target_url}")

        stream_url = get_stream_url(target_url)

        if stream_url:
            file_path = os.path.join(OUTPUT_FOLDER, "{}.m3u8".format(sanitize(name)))
            save_m3u8(file_path, stream_url, name)
            print(f"    [OK] Kaydedildi -> {file_path}")
            success_count += 1
        else:
            print(f"    [FAIL] Basarisiz — {name}")
            fail_count += 1
            failed_names.append(name)

    # ─── Birleşik liste ──────────────────────────────────────
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV2_COMBINED.m3u")
    lines = ["#EXTM3U\n"]
    for m3u8_file in sorted(os.listdir(OUTPUT_FOLDER)):
        if m3u8_file.endswith(".m3u8") and not m3u8_file.startswith("_"):
            full = os.path.join(OUTPUT_FOLDER, m3u8_file)
            with open(full, encoding="utf-8") as f:
                content = f.read()
            body = re.sub(r'^#EXTM3U\n?', '', content).strip()
            lines.append(body + "\n")

    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ─── Özet ───────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("TAMAMLANDI  OK:{} FAIL:{}".format(success_count, fail_count))
    if failed_names:
        print("Basarisiz kanallar:")
        for n in failed_names:
            print("  - {}".format(n))
    print("[+] Birlesik liste -> {}".format(combined_path))


if __name__ == "__main__":
    main()
