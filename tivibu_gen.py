import requests
import json

# 🔥 BURAYA İSTERSEN PROXY EKLE
# Örn: "https://senin-worker.workers.dev/?url="
PROXY = ""  

def safe_json(resp):
    try:
        return resp.json()
    except:
        print("❌ JSON parse hatası")
        print(resp.text[:300])
        return None

def fetch(url, headers):
    try:
        full_url = PROXY + url if PROXY else url
        r = requests.get(full_url, headers=headers, timeout=15)

        print(f"➡️ {url}")
        print("STATUS:", r.status_code)

        if r.status_code != 200:
            print("❌ HTTP hata:", r.status_code)
            print(r.text[:200])
            return None

        # JSON kontrol
        if "application/json" not in r.headers.get("Content-Type", ""):
            print("❌ JSON değil! Gelen veri:")
            print(r.text[:300])
            return None

        return safe_json(r)

    except Exception as e:
        print("❌ İstek hatası:", e)
        return None


def get_m3u():
    list_url = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getchannellist.jsp?columncode=020000&pageno=1&numperpage=500&ordertype=1&isqueryfavorite=1&isqueryprevue=1&ischecklock=1"

    play_url = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getppvtvplayurl.jsp?channelcode={}&columncode=030000&urlredirect=1&playtype=0&productcode=5237"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://www.tivibu.com.tr/",
        "Origin": "https://www.tivibu.com.tr",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Connection": "keep-alive"
    }

    data = fetch(list_url, headers)

    if not data:
        print("❌ Kanal listesi alınamadı")
        return

    channels = data.get("data", [])

    if not channels:
        print("❌ Kanal listesi boş")
        return

    m3u = "#EXTM3U\n"

    for ch in channels:
        name = ch.get("channelname", "Bilinmeyen")
        code = ch.get("channelcode", "")

        if not code:
            continue

        p_data = fetch(play_url.format(code), headers)

        if not p_data:
            continue

        stream = p_data.get("playurl") or p_data.get("httpsplayurl")

        if stream:
            print(f"✅ {name}")
            m3u += f'#EXTINF:-1 tvg-id="{code}" tvg-name="{name}",{name}\n'
            m3u += stream + "\n"
        else:
            print(f"⚠️ Stream yok: {name}")

    # Dosya yaz
    with open("tbu.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("🎉 tbu.m3u oluşturuldu!")


if __name__ == "__main__":
    get_m3u()
