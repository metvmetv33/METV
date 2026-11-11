# -*- coding: utf-8 -*-
import requests
import json
import time
import urllib.parse

def main():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'AirTV-STB/1.0.0',
        'Accept': 'application/json',
        'Accept-Language': 'tr-TR,tr;q=0.8',
        'Referer': 'http://geil.to/'
    })
    
    # 1. Önce grupları/ülkeleri dinamik olarak almayı deneyelim veya standart listeyi kullanalım
    # PHP kodundaki mantığa göre temel grupları belirleyebiliriz.
    # Alternatif olarak grupları test etmek için bilinen popüler grupları listeleyebiliriz:
    search_groups = [
        'Turkey', 'Germany', 'United Kingdom', 'France', 'Spain', 
        'Italy', 'Netherlands', 'Poland', 'Portugal', 'Romania', 
        'Russia', 'Balkans', 'Albania', 'Bulgaria', 'Croatia', 'Arabia'
    ]

    m3u_lines = ["#EXTM3U"]
    full_json_data = {}
    cursors = [0, 300, 600, 900]

    for group in search_groups:
        full_json_data[group] = []
        channels = {}
        print(f"Lade Gruppe: {group}...", end="", flush=True)

        for cursor in cursors:
            params = {
                'region': 'TR',
                'language': 'tr',
                'sort': 'name',
                'filter[group]': group,
                'cursor': cursor
            }

            url = 'http://geil.to/live/catalog/live/channels.json?' + urllib.parse.urlencode(params, safe='')

            try:
                r = session.get(url, timeout=25)
                
                if r.status_code == 200:
                    data = r.json()
                    items = data.get("items", [])
                    
                    if not items:
                        break  # Bu cursor'dan sonra veri yoksa döngüyü kır
                        
                    for item in items:
                        channel_id = item.get('id')
                        name = item.get('name', '')
                        
                        if not channel_id or not name:
                            continue
                            
                        channel_id = str(channel_id)
                        name = name.replace("\r", " ").replace("\n", " ").strip()
                        
                        if not name:
                            name = channel_id
                            
                        channels[channel_id] = name
                else:
                    break
            except Exception as e:
                break

        # Bulunan kanalları listeye ve m3u formatına ekleme
        for channel_id, name in channels.items():
            # M3U satırları
            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
            # PHP kodundaki proxy/oynatıcı yapısına benzer link yapısı
            stream_url = f'http://sultanios.alwaysdata.net/vavo.php?ID={urllib.parse.quote(channel_id)}'
            m3u_lines.append(stream_url)
            
            # JSON verisi
            full_json_data[group].append({
                "id": channel_id,
                "name": name,
                "url": stream_url,
                "group": group
            })

        print(f" Fertig ({len(channels)} Kanäle)")
        time.sleep(0.05)

    # Dosyalara kaydetme
    with open("vavoo_all.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    with open("vavoo_full.json", "w", encoding="utf-8") as f:
        json.dump(full_json_data, f, ensure_ascii=False, indent=4)
        
    print("\nUpdate abgeschlossen. Alle Kanäle wurden exportiert.")

if __name__ == "__main__":
    main()
