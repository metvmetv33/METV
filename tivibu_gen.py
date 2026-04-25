import requests
import json

def get_m3u():
    list_url = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getchannellist.jsp?columncode=020000&pageno=1&numperpage=500&ordertype=1&isqueryfavorite=1&isqueryprevue=1&ischecklock=1"
    play_url_base = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getppvtvplayurl.jsp?channelcode={}&columncode=030000&urlredirect=1&playtype=0&productcode=5237"

    # Daha gerçekçi tarayıcı başlıkları
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': 'https://www.tivibu.com.tr/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }
    
    try:
        response = requests.get(list_url, headers=headers, timeout=15)
        
        # Yanıtın JSON olup olmadığını kontrol et
        if response.status_code != 200:
            print(f"Sunucu hatası: {response.status_code}")
            return

        data = response.json()
        channels = data.get('data', [])
        
        m3u_content = "#EXTM3U\n"
        
        if not channels:
            print("Kanal listesi boş döndü.")
            return

        for ch in channels:
            ch_name = ch.get('channelname', 'Bilinmeyen Kanal')
            ch_code = ch.get('channelcode', '')
            
            if ch_code:
                try:
                    p_res = requests.get(play_url_base.format(ch_code), headers=headers, timeout=10)
                    p_data = p_res.json()
                    stream_url = p_data.get('playurl', p_data.get('httpsplayurl', ''))
                    
                    if stream_url:
                        m3u_content += f'#EXTINF:-1 tvg-id="{ch_code}" tvg-name="{ch_name}",{ch_name}\n'
                        m3u_content += f'{stream_url}\n'
                except:
                    continue
        
        with open("tbu.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print("tbu.m3u başarıyla güncellendi.")

    except Exception as e:
        print(f"Hata detayı: {e}")

if __name__ == "__main__":
    get_m3u()
