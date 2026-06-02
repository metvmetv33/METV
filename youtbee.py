import subprocess
import requests
import re
import os
import time
from typing import Optional

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL      = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
OUTPUT_FOLDER = "metv2"
MAX_RETRIES   = 2
WAIT_TIME     = 3
# GitHub Actions: COOKIES_FILE ortam değişkeninden okunur
# Lokal: cookies.txt dosyasını yanına koy
COOKIES_FILE  = os.environ.get("YT_COOKIES_FILE", "cookies.txt")
# ───────────────────────────────────────────────────────────


def get_channels():
    # type: () -> list
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


def build_cmd(channel_url):
    # type: (str) -> list
    """yt-dlp komut listesini oluştur."""
    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "--no-warnings",
        "--quiet",
        "-f", "best",
        "-g",
        "--no-playlist",
        # Bot koruması için ekstra ayarlar
        "--extractor-args", "youtube:skip=hls,dash",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    ]

    # cookies.txt varsa ekle (bot korumasını aşar)
    if os.path.isfile(COOKIES_FILE):
        print("    [cookies] {} kullaniliyor".format(COOKIES_FILE))
        cmd += ["--cookies", COOKIES_FILE]
    else:
        print("    [!] cookies.txt bulunamadi — bot korumasi asilmayabilir")

    cmd.append(channel_url)
    return cmd


def get_stream_url(channel_url):
    # type: (str) -> Optional[str]
    cmd = build_cmd(channel_url)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            # Başarılı çıktıdan URL'yi al
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line.startswith("http"):
                    return line

            # Hata mesajını göster
            err_lines = result.stderr.strip().splitlines()
            hint = next((l for l in err_lines if "ERROR" in l), "")
            if not hint:
                hint = next((l for l in err_lines if l.strip()), "")
            print("    Deneme {}/{}: {}".format(attempt, MAX_RETRIES, hint[:130]))

        except subprocess.TimeoutExpired:
            print("    Deneme {}/{}: Zaman asimi (60s)".format(attempt, MAX_RETRIES))
        except FileNotFoundError:
            print("[!] 'yt-dlp' bulunamadi! Kurun: pip install yt-dlp")
            return None
        except Exception as e:
            print("    Deneme {}/{}: Hata — {}".format(attempt, MAX_RETRIES, e))

        if attempt < MAX_RETRIES:
            time.sleep(WAIT_TIME)

    return None


def sanitize(name):
    # type: (str) -> str
    return re.sub(r'[^\w\s\-]', '', name).strip().replace(" ", "_")


def save_m3u8(file_path, stream_url, channel_name, logo_url=""):
    # type: (str, str, str, str) -> None
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
    # Cookies dosyası yoksa kullanıcıyı uyar
    if not os.path.isfile(COOKIES_FILE):
        print("=" * 60)
        print("UYARI: cookies.txt bulunamadi!")
        print("YouTube bot korumasi nedeniyle cogu kanal basarisiz olacak.")
        print("Cozum icin README'ye bakin.")
        print("=" * 60)

    channels = get_channels()
    if not channels:
        print("[!] Kanal listesi bos, cikiliyor.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("[*] Dosyalar '{}/'' klasorune kaydedilecek.\n".format(OUTPUT_FOLDER))

    success_count = 0
    fail_count    = 0
    failed_names  = []

    for i, ch in enumerate(channels, 1):
        name       = ch.get("name", "Kanal_{}".format(i))
        target_url = ch.get("url", "").strip()
        logo_url   = ch.get("logo", "")

        if not target_url:
            print("[{}/{}] '{}': URL yok, atlaniyor.".format(i, len(channels), name))
            continue

        print("[{}/{}] {}".format(i, len(channels), name))
        print("    URL: {}".format(target_url))

        stream_url = get_stream_url(target_url)

        if stream_url:
            file_path = os.path.join(OUTPUT_FOLDER, "{}.m3u8".format(sanitize(name)))
            save_m3u8(file_path, stream_url, name, logo_url)
            print("    [OK] -> {}".format(file_path))
            success_count += 1
        else:
            print("    [FAIL] {}".format(name))
            fail_count += 1
            failed_names.append(name)

    # ─── Birleşik liste ──────────────────────────────────
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV2_COMBINED.m3u")
    header = "#EXTM3U\n"
    entries = []

    for m3u8_file in sorted(os.listdir(OUTPUT_FOLDER)):
        if not m3u8_file.endswith(".m3u8") or m3u8_file.startswith("_"):
            continue
        full = os.path.join(OUTPUT_FOLDER, m3u8_file)
        with open(full, encoding="utf-8") as f:
            content = f.read()
        body = re.sub(r'^#EXTM3U\n?#EXT-X-VERSION:[0-9]\n?', '', content).strip()
        entries.append(body)

    with open(combined_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(entries) + "\n")

    # ─── Özet ────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("TAMAMLANDI   OK:{}   FAIL:{}   TOPLAM:{}".format(
        success_count, fail_count, success_count + fail_count))
    if failed_names:
        print("\nBasarisiz kanallar ({}):" .format(len(failed_names)))
        for n in failed_names:
            print("  - {}".format(n))
    print("\n[+] Birlesik liste -> {}".format(combined_path))


if __name__ == "__main__":
    main()
