# -*- coding: utf-8 -*-
import requests
import json

def main():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'MediaHubMX/3.0.2',
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8'
    })
    
    target_url = "https://withered-shape-3305.vadimkantorov.workers.dev/?https://www2.vavoo.to/live2/index?output=json"
    
    print("Kanal listesi indiriliyor...")
    try:
        response = session.get(target_url, timeout=30)
        if response.status_code != 200:
            print(f"Hata: Sunucu {response.status_code} kodu döndürdü.")
            return
            
        items = response.json()
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return

    m3u_lines = ["#EXTM3U"]
    full_json_data = {}
    
    # Gelen verileri gruplarına göre düzenleme
    for item in items:
        group = item.get("group", "Uncategorized")
        name = item.get("name", "Unknown")
        tvg_id = item.get("tvg_id", "")
        logo = item.get("logo", "")
        url = item.get("url", "")
        
        if not url:
            continue
            
        if group not in full_json_data:
            full_json_data[group] = []
            
        # JSON verisine ekle
        full_json_data[group].append({
            "name": name,
            "tvg_id": tvg_id,
            "logo": logo,
            "url": url,
            "group": group
        })
        
        # M3U satırlarına ekle (logo ve tvg_id bilgileriyle beraber)
        extinf_line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}'
        m3u_lines.append(extinf_line)
        m3u_lines.append(url)

    # Dosyalara kaydetme
    with open("vavoo_direct.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    with open("vavoo_direct.json", "w", encoding="utf-8") as f:
        json.dump(full_json_data, f, ensure_ascii=False, indent=4)
        
    print("\nİşlem başarılı!")
    print(f"Toplam {len(items)} kanal işlendi.")
    print("Dosyalar kaydedildi: vavoo_direct.m3u ve vavoo_direct.json")

if __name__ == "__main__":
    main()
