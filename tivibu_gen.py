import requests
import time

JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/tibu.json"

PLAY_API = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getppvtvplayurl.jsp"

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.tivibu.com.tr/",
    "Origin": "https://www.tivibu.com.tr",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

def get_play_url(code):
    params = {
        "channelcode": code,
        "columncode": "030000",
        "urlredirect": "1",
        "playtype": "0",
        "productcode": "5237"
    }

    try:
        r = session.get(PLAY_API, headers=headers, params=params, timeout=10)

        if r.status_code != 200:
            return None

        # JSON değilse atla
        if "application/json" not in r.headers.get("Content-Type", ""):
            print("❌ JSON değil:", code)
            return None

        data = r.json()

        return data.get("httpsplayurl") or data.get("playurl")

    except:
        return None


def main():
    print("JSON indiriliyor...")
    r = requests.get(JSON_URL, timeout=15)

    if r.status_code != 200:
        print("❌ JSON alınamadı")
        return

    data = r.json()
    channels = data.get("data", [])

    m3u = "#EXTM3U\n"

    print(f"Toplam kanal: {len(channels)}")

    for ch in channels:
        name = ch.get("channelname", "Bilinmeyen")
        code = ch.get("channelcode", "")

        if not code:
            continue

        print(f"🔄 {name}")

        url = get_play_url(code)

        if url:
            print(f"✅ OK")
            m3u += f'#EXTINF:-1 tvg-id="{code}" tvg-name="{name}",{name}\n'
            m3u += url + "\n"
        else:
            print("❌ alınamadı")

        time.sleep(0.5)  # ban yememek için

    with open("tbu.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("🎉 M3U hazır!")


if __name__ == "__main__":
    main()
