import os
import re
import time
from typing import Optional
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL      = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
OUTPUT_FOLDER = "metv"
MAX_RETRIES   = 2
WAIT_TIME     = 3
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


def get_stream_url(channel_url):
    # type: (str) -> Optional[str]
    channel_id_match = re.search(r"channel/(UC[a-zA-Z0-9_\-]+)", channel_url)
    if channel_id_match:
        channel_id = channel_id_match.group(1)
    else:
        channel_id = channel_url.strip().rstrip("/").split("/")[-1].replace("live", "").strip("/")

    shared_headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )
    }

    session = requests.Session()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            home_resp = session.get(
                "https://ytdlp.online/tr/",
                headers=shared_headers,
                timeout=15,
                verify=False
            )
            cookies_dict = home_resp.cookies.get_dict()
            session_cookie = cookies_dict.get("session")

            if not session_cookie:
                set_cookie_header = home_resp.headers.get("set-cookie", "")
                m = re.search(r"session=([^;]+)", set_cookie_header, re.IGNORECASE)
                if m:
                    session_cookie = m.group(1)

            if not session_cookie:
                print("    Deneme {}/{}: Session alinamadi (HTTP {})".format(
                    attempt, MAX_RETRIES, home_resp.status_code))
                time.sleep(WAIT_TIME)
                continue

            # itag 91-95 = ses+video birleşik HLS (muxed)
            command = (
                '-f "95/94/93/92/91/best[acodec!=none]" '
                '--get-url https://m.youtube.com/channel/{}/live'.format(channel_id)
            )
            encoded_command = requests.utils.quote(command)
            api_url = "https://ytdlp.online/api/v1/stream?command={}".format(encoded_command)

            stream_headers = {
                "accept":     "text/event-stream",
                "cookie":     "session={}".format(session_cookie),
                "referer":    "https://ytdlp.online/tr/",
                "user-agent": shared_headers["user-agent"],
            }

            stream_resp = session.get(
                api_url, headers=stream_headers, timeout=40, verify=False
            )

            if stream_resp.status_code != 200:
                print("    Deneme {}/{}: HTTP {}".format(
                    attempt, MAX_RETRIES, stream_resp.status_code))
                time.sleep(WAIT_TIME)
                continue

            text = stream_resp.text

            # hls_playlist URL'si (itag 91-95 = muxed ses+video)
            m = re.search(
                r"(https://manifest\.googlevideo\.com/api/manifest/hls_playlist/[^\s\"'<>\n]+)",
                text
            )
            if m:
                return m.group(1)

            # hls_variant (tüm kaliteler, master playlist)
            m2 = re.search(
                r"(https://manifest\.googlevideo\.com/api/manifest/hls_variant/[^\s\"'<>\n]+)",
                text
            )
            if m2:
                return m2.group(1)

            print("    Deneme {}/{}: URL bulunamadi.".format(attempt, MAX_RETRIES))

        except Exception as e:
            print("    Deneme {}/{}: Hata — {}".format(attempt, MAX_RETRIES, str(e)[:80]))

        if attempt < MAX_RETRIES:
            time.sleep(WAIT_TIME)

    return None


def sanitize_filename(name):
    # type: (str) -> str
    """Dosya adı için Türkçe karakterleri ASCII'ye çevir, geçersizleri kaldır."""
    tr_map = str.maketrans("ığüşöçİĞÜŞÖÇ", "igusocIGUSOC")
    name = name.translate(tr_map)
    name = re.sub(r"[^\w\s\-]", "", name).strip().replace(" ", "_")
    return name


def main():
    channels = get_channels()
    if not channels:
        print("[!] Kanal listesi bos, cikiliyor.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("[*] Dosyalar '{}/' klasorune kaydedilecek.\n".format(OUTPUT_FOLDER))

    # Başarılı kanalları birleşik liste için tut
    combined_entries = []

    success_count = 0
    fail_count    = 0
    failed_names  = []

    for i, ch in enumerate(channels, 1):
        name       = ch.get("name", "Kanal_{}".format(i))
        target_url = ch.get("url", "").strip()
        logo_url   = ch.get("logo", "")

        if not target_url:
            continue

        print("[{}/{}] {}".format(i, len(channels), name))

        stream_url = get_stream_url(target_url)

        if stream_url:
            safe_name = sanitize_filename(name)

            # ── Bireysel .m3u8 dosyası ──────────────────────────
            # Sadece stream URL — oynatıcılar bu formatı doğrudan açar
            file_path = os.path.join(OUTPUT_FOLDER, "{}.m3u8".format(safe_name))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(stream_url + "\n")

            # ── Combined listeye ekle ────────────────────────────
            logo_attr = ' tvg-logo="{}"'.format(logo_url) if logo_url else ""
            extinf = '#EXTINF:-1 tvg-name="{name}"{logo},{name}'.format(
                name=name, logo=logo_attr
            )
            combined_entries.append("{}\n{}".format(extinf, stream_url))

            itag_m = re.search(r"/itag/(\d+)", stream_url)
            itag   = itag_m.group(1) if itag_m else "?"
            print("    [OK] itag={} -> {}".format(itag, file_path))
            success_count += 1
        else:
            print("    [FAIL] -> {}".format(name))
            fail_count += 1
            failed_names.append(name)

        time.sleep(1)

    # ── Birleşik _METV_COMBINED.m3u ─────────────────────────────
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV_COMBINED.m3u")
    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(combined_entries))
        f.write("\n")

    print("\n" + "=" * 55)
    print("TAMAMLANDI   OK:{}   FAIL:{}   TOPLAM:{}".format(
        success_count, fail_count, success_count + fail_count))
    if failed_names:
        print("\nCozulemeyen kanallar ({}):".format(len(failed_names)))
        for n in failed_names:
            print("  - {}".format(n))
    print("\n[+] Birlesik IPTV Listesi -> {}".format(combined_path))
    print("[+] Oynatici icin kullan: https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/{}/{}".format(
        OUTPUT_FOLDER, "_METV_COMBINED.m3u"
    ))


if __name__ == "__main__":
    main()
