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
    
    for item in items:
        group = item.get("group", "Uncategorized")
        name = item.get("name", "Unknown")
        tvg_id = item.get("tvg_id", "")
        logo = item.get("logo", "")
        
        # Orijinal URL'den veya tvg_id / ID kısmından istenen formatı oluşturalım
        # Örn: https://vavoo.to/vavoo-iptv/play/17029379329ed4b84db05f
        original_url = item.get("url", "")
        if not original_url:
            continue
            
        # URL'in son kısmındaki dosya adını/ID'yi alıyoruz (örn: 51258455.m3u8 -> 51258455)
        # Eğer doğrudan API'den gelen URL yapısı kullanılsın isterseniz aşağıdaki dönüşüm yapılır:
        # Örnek: https://vavoo.to/live2/play3/51258455.m3u8 -> 51258455
        file_part = original_url.split('/')[-1].replace('.m3u8', '')
        
        # İstediğiniz özel format
        custom_url = f"https://vavoo.to/vavoo-iptv/play/{file_part}"
            
        if group not in full_json_data:
            full_json_data[group] = []
            
        full_json_data[group].append({
            "name": name,
            "tvg_id": tvg_id,
            "logo": logo,
            "url": custom_url,
            "group": group
        })
        
        extinf_line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}'
        m3u_lines.append(extinf_line)
        m3u_lines.append(custom_url)

    # Dosyaları kaydediyoruz
    with open("vavoo_all.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    with open("vavoo_full.json", "w", encoding="utf-8") as f:
        json.dump(full_json_data, f, ensure_ascii=False, indent=4)
        
    print("\nİşlem başarılı!")
    print(f"Toplam {len(items)} kanal işlendi.")
    print("Dosyalar güncellendi: vavoo_all.m3u ve vavoo_full.json")

if __name__ == "__main__":
    main()
