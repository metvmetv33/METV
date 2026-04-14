import requests
import json
import os
import time

COUNTRIES = [
    "Turkey","France","Germany","Italy","Spain",
    "United Kingdom","Albania","Arabia","Balkans",
    "Bulgaria","Netherlands","Poland","Portugal",
    "Romania","Russia"
]

def get_signature():
    try:
        r = requests.post(
            "https://www.vavoo.tv/api/app/ping",
            json={
                "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
                "reason": "app-blur",
                "locale": "de",
                "metadata": {
                    "device": {"type": "Handset"},
                    "os": {"name": "android"},
                    "app": {"platform": "android"}
                }
            },
            headers={"user-agent": "okhttp/4.11.0"},
            timeout=20
        )

        print("[DEBUG] SIG STATUS:", r.status_code)
        print("[DEBUG] SIG TEXT:", r.text[:200])

        return r.json().get("addonSig")

    except Exception as e:
        print("[SIGNATURE ERROR]", e)
        return None


def get_channels(sig, country):
    headers = {
        "user-agent": "okhttp/4.11.0",
        "mediahubmx-signature": sig
    }

    cursor = 0
    all_items = []

    while True:
        try:
            r = requests.post(
                "https://vavoo.tv/mediahubmx-catalog.json",
                json={
                    "catalogId": "iptv",
                    "id": "iptv",
                    "cursor": cursor,
                    "filter": {"group": country}
                },
                headers=headers,
                timeout=20
            )

            print(f"[DEBUG] {country} status:", r.status_code)
            print("[DEBUG] RESPONSE:", r.text[:150])

            if not r.text.strip():
                break

            data = r.json()

            if "items" not in data:
                break

            all_items += data["items"]

            if not data.get("nextCursor"):
                break

            cursor = data["nextCursor"]

        except Exception as e:
            print("[CHANNEL ERROR]", country, e)
            break

    return all_items


def save(country, items):
    if not items:
        print(f"⚠️ {country} BOŞ")
        return

    with open(f"{country}.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in items:
            if not ch.get("url"):
                continue

            name = ch.get("name", "Unknown")

            if isinstance(ch.get("ids"), dict):
                url = f"https://vavoo.to/vavoo-iptv/play/{ch['ids'].get('id','')}"
            else:
                url = ch["url"]

            f.write(f'#EXTINF:-1 group-title="{country}",{name}\n')
            f.write(url + "\n")


def main():
    sig = get_signature()

    if not sig:
        print("❌ SIGNATURE FAIL → EXIT")
        return

    for c in COUNTRIES:
        print("\n🌍", c)

        items = get_channels(sig, c)

        print(f"📦 {c} channels:", len(items))

        save(c, items)

        time.sleep(2)


if __name__ == "__main__":
    main()
