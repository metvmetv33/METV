import os
import re
import time
from typing import Optional
import requests

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL = (
    "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
)
OUTPUT_FOLDER = "metv2"
MAX_RETRIES = 2
WAIT_TIME = 3

# Link çözücü web servis ayarları
API_URL = "https://api.ytdlp.online/api/v1/stream"  # Örnek API endpoint (Sitenin arka plan API yapısına göre güncellenmelidir)
# ───────────────────────────────────────────────────────────


def get_channels():
    print("[*] Kanal listesi cekiliyor: {}".format(JSON_URL))
    try:
        r = requests.get(JSON_URL, timeout=20)
        r.raise_for_status()
        data = r.json()
        print("[+] {} kanal bulundu.".format(len(data)))
        return data
    except Exception as e:
        print("[!] Liste alinamadi: {}".format(e))
        return []


def get_stream_url_from_web(channel_url):
    # type: (str) -> Optional[str]
    """yt-dlp.online API'sini kullanarak stream URL'ini yakalar."""
    payload = {
        "url": channel_url,
        "format": "best",
        "skip_hls_dash": True,  # Sitenin desteklediği parametrelere göre ayarlanır
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Not: Sitenin API yapısı POST veya GET kabul ediyor olabilir.
            # Genelde bu tür servisler POST isteği ile URL alır.
            response = requests.post(
                API_URL, json=payload, headers=headers, timeout=30
            )

            if response.status_code == 200:
                res_data = response.json()
                # API çıktısına göre buradaki dict anahtarı (örn: 'url', 'stream_url', 'data') değişebilir.
                stream_url = res_data.get("url") or res_data.get("stream_url")
                if stream_url and stream_url.startswith("http"):
                    return stream_url

            print(
                "    Deneme {}/{}: Sunucu hatası kodu -> {}".format(
                    attempt, MAX_RETRIES, response.status_code
                )
            )

        except Exception as e:
            print("    Deneme {}/{}: Web hatasi — {}".format(attempt, MAX_RETRIES, e))

        if attempt < MAX_RETRIES:
            time.sleep(WAIT_TIME)

    return None


def sanitize(name):
    return re.sub(r"[^\w\s\-]", "", name).strip().replace(" ", "_")


def save_m3u8(file_path, stream_url, channel_name, logo_url=""):
    tvg_logo = ' tvg-logo="{}"'.format(logo_url) if logo_url else ""
    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        '#EXTINF:-1 tvg-name="{name}"{logo},{name}\n'
        "{url}\n"
    ).format(name=channel_name, logo=tvg_logo, url=stream_url)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    channels = get_channels()
    if not channels:
        print("[!] Kanal listesi bos, cikiliyor.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("[*] Dosyalar '{}/'' klasorune kaydedilecek.\n".format(OUTPUT_FOLDER))

    success_count = 0
    fail_count = 0
    failed_names = []

    for i, ch in enumerate(channels, 1):
        name = ch.get("name", "Kanal_{}".format(i))
        target_url = ch.get("url", "").strip()
        logo_url = ch.get("logo", "")

        if not target_url:
            print(
                "[{}/{}] '{}': URL yok, atlaniyor.".format(
                    i, len(channels), name
                )
            )
            continue

        print("[{}/{}] {}".format(i, len(channels), name))
        print("    Yayin URL: {}".format(target_url))

        # Yerel komut yerine Web API kullanılıyor
        stream_url = get_stream_url_from_web(target_url)

        if stream_url:
            file_path = os.path.join(
                OUTPUT_FOLDER, "{}.m3u8".format(sanitize(name))
            )
            save_m3u8(file_path, stream_url, name, logo_url)
            print("    [OK] -> {}".format(file_path))
            success_count += 1
        else:
            print("    [FAIL] {}".format(name))
            fail_count += 1
            failed_names.append(name)

    # ─── Birleşik liste oluşturma ─────────────────────────
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV2_COMBINED.m3u")
    header = "#EXTM3U\n"
    entries = []

    for m3u8_file in sorted(os.listdir(OUTPUT_FOLDER)):
        if not m3u8_file.endswith(".m3u8") or m3u8_file.startswith("_"):
            continue
        full = os.path.join(OUTPUT_FOLDER, m3u8_file)
        with open(full, encoding="utf-8") as f:
            content = f.read()
        body = re.sub(r"^#EXTM3U\n?#EXT-X-VERSION:[0-9]\n?", "", content).strip()
        entries.append(body)

    with open(combined_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(entries) + "\n")

    # ─── Özet ────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(
        "TAMAMLANDI   OK:{}   FAIL:{}   TOPLAM:{}".format(
            success_count, fail_count, success_count + fail_count
        )
    )
    if failed_names:
        print("\nBasarisiz kanallar ({}):".format(len(failed_names)))
        for n in failed_names:
            print("  - {}".format(n))
    print("\n[+] Birlesik liste -> {}".format(combined_path))


if __name__ == "__main__":
    main()
