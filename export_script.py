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
                        break  
                        
                    for item in items:
                        channel_id = item.get('id')
                        name = item.get('name', '')
                        stream_url = item.get('url', '') # Doğrudan API'den gelen gerçek akış linki
                        
                        if not channel_id or not name or not stream_url:
                            continue
                            
                        channel_id = str(channel_id)
                        name = name.replace("\r", " ").replace("\n", " ").strip()
                        
                        if not name:
                            name = channel_id
                            
                        channels[channel_id] = {
                            "name": name,
                            "url": stream_url
                        }
                else:
                    break
            except Exception as e:
                break

        # Doğrudan gerçek URL'leri ekleme
        for channel_id, info in channels.items():
            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{info["name"]}')
            m3u_lines.append(info["url"])  # Proxy linki yerine doğrudan asıl kaynak linki
            
            full_json_data[group].append({
                "id": channel_id,
                "name": info["name"],
                "url": info["url"],
                "group": group
            })

        print(f" Fertig ({len(channels)} Kanäle)")
        time.sleep(0.05)

    # Dosyalara kaydetme
    with open("vavoo_all.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    with open("vavoo_full.json", "w", encoding="utf-8") as f:
        json.dump(full_json_data, f, ensure_ascii=False, indent=4)
        
    print("\nİşlem tamamlandı. Tüm kanallar doğrudan kaynak linkleriyle kaydedildi.")

if __name__ == "__main__":
    main()
