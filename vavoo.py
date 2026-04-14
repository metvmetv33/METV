import requests
import json
import time
import os

BASE_DIR = os.path.dirname(__file__)

with open(os.path.join(BASE_DIR, "countries.json"), encoding="utf-8") as f:
    COUNTRIES = json.load(f)


def get_signature():
    url = "https://www.vavoo.tv/api/app/ping"

    payload = {
        "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
        "reason": "app-blur",
        "locale": "de",
        "metadata": {
            "device": {"type": "Handset"},
            "os": {"name": "android"},
            "app": {"platform": "android"}
        }
    }

    headers = {
        "user-agent": "okhttp/4.11.0",
        "content-type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers, timeout=15)
    return r.json().get("addonSig")


def get_channels(signature, country):
    headers = {
        "user-agent": "okhttp/4.11.0",
        "content-type": "application/json",
        "mediahubmx-signature": signature
    }

    channels = []
    cursor = 0

    while True:
        data = {
            "catalogId": "iptv",
            "id": "iptv",
            "filter": {"group": country},
            "cursor": cursor
        }

        r = requests.post(
            "https://vavoo.tv/mediahubmx-catalog.json",
            json=data,
            headers=headers,
            timeout=15
        )

        js = r.json()

        if "items" not in js:
            break

        channels.extend(js["items"])

        if not js.get("nextCursor"):
            break

        cursor = js["nextCursor"]

    return channels


def resolve_link(url, ch):
    if isinstance(ch.get("ids"), dict) and ch["ids"].get("id"):
        return f"https://vavoo.to/vavoo-iptv/play/{ch['ids']['id']}"
    return url


def save_m3u(country, channels):
    filename = f"{country.replace(' ', '_')}.m3u"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in channels:
            if not ch.get("url"):
                continue

            name = ch.get("name", "Unknown")
            link = resolve_link(ch["url"], ch)

            f.write(f'#EXTINF:-1 group-title="{country}",{name}\n')
            f.write(link + "\n")

    print(f"✅ {filename} oluşturuldu ({len(channels)} kanal)")


def main():
    print("🔑 Signature alınıyor...")
    sig = get_signature()

    if not sig:
        print("❌ Signature alınamadı")
        return

    for country in COUNTRIES:
        print(f"🌍 {country} çekiliyor...")
        channels = get_channels(sig, country)

        if not channels:
            print(f"⚠️ {country} boş geldi")
            continue

        save_m3u(country, channels)
        time.sleep(2)


if __name__ == "__main__":
    main()
