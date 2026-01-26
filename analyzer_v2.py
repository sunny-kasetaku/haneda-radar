from datetime import datetime, timedelta

def analyze_demand(flights, current_time=None):
    # 日本時間現在時刻
    if current_time is None:
        now = datetime.utcnow() + timedelta(hours=9)
    else:
        now = current_time
    
    # 【設定】黄金比 (過去60分 / 未来30分)
    PAST_MINUTES = 60
    FUTURE_MINUTES = 30

    start_time = now - timedelta(minutes=PAST_MINUTES)
    end_time = now + timedelta(minutes=FUTURE_MINUTES)
    
    filtered_flights = []
    hourly_counts = {} 
    
    seen_flights = set()

    for f in flights:
        arr_time_str = f.get('arrival_time', '')
        if not arr_time_str: continue
        
        try:
            dt_str = arr_time_str[:19] 
            f_dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            f_dt_jst = f_dt 
        except:
            continue

        # 【重複対策 / コードシェア排除】
        dep = f.get('departure', {})
        if not dep: dep = {}
        # IATAがない場合、空港名(airport)が入る。
        origin_code = dep.get('iata') or dep.get('airport') or "UNK"
        f['origin_iata'] = origin_code 
        
        unique_key = f"{dt_str}_{origin_code}"

        if unique_key in seen_flights:
            continue
        seen_flights.add(unique_key)

        # 1. リアルタイムリストへの振り分け
        if start_time <= f_dt_jst <= end_time:
            pax = estimate_pax(f)
            f['pax_estimated'] = pax
            filtered_flights.append(f)

        # 2. 未来予測用の集計
        h = f_dt_jst.hour
        pax = estimate_pax(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax

    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # 2. ターミナル別集計
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        t_str = str(f.get('terminal', ''))
        airline = str(f.get('airline', '')).lower()
        pax = f.get('pax_estimated', 0)
        
        # 国際線判定 (T3 または 250名以上)
        if t_str == '3' or pax >= 250:
            terminal_counts["国際(T3)"] += pax
            
        elif t_str == '2':
            # T2 (ANA系) 偶数・奇数判定
            try: 
                f_num_raw = str(f.get('flight_number', '0'))
                num = int(''.join(filter(str.isdigit, f_num_raw)))
            except: 
                num = 0
            
            if num % 2 == 0: terminal_counts["3号(T2)"] += pax
            else: terminal_counts["4号(T2)"] += pax
            
        elif t_str == '1':
            # T1 (JAL系) 北・南判定
            if 'japan airlines' in airline or 'jal' in airline: 
                terminal_counts["2号(T1北)"] += pax
            else: 
                terminal_counts["1号(T1南)"] += pax
        else:
            terminal_counts["国際(T3)"] += pax

    # 3. 未来予測データ作成
    forecast_data = {}
    for i in range(0, 3):
        target_h = (now.hour + i) % 24
        count = hourly_counts.get(target_h, 0)
        
        if count >= 1000: status, comment = "🔥 高", "確変中"
        elif count >= 300: status, comment = "👀 通常", "需要あり"
        else: status, comment = "📉 低", "静か"

        forecast_data[f"h{i+1}"] = {
            "label": f"{target_h:02d}:00〜",
            "pax": count,
            "status": status,
            "comment": comment
        }

    return {
        "flights": filtered_flights,
        "unique_count": len(filtered_flights),
        "setting_past": PAST_MINUTES,
        "setting_future": FUTURE_MINUTES,
        **terminal_counts,
        "forecast": forecast_data
    }

def estimate_pax(flight):
    """
    乗客数を推定する。
    IATAコードだけでなく、空港名(英語)もチェックして国内線を正しく判定する。
    表記揺れ（Shi/Si, Tsu/Tu, O/Ou）にも対応。
    """
    term = str(flight.get('terminal', ''))
    origin_val = flight.get('origin_iata', '')
    
    # 1. 3文字コードリスト
    domestic_codes = [
        "CTS", "FUK", "OKA", "ITM", "KIX", "NGO", "KMQ", "HKD", "HIJ", "MYJ",
        "KCZ", "TAK", "KMJ", "KMI", "KOJ", "ISG", "MMY", "IWK", "UBJ", "TKS",
        "AOJ", "MSJ", "OIT", "AXT", "GAJ", "OKJ", "NGS", "AKJ", "OBO", "SHM",
        "ASJ", "MMB", "IZO", "KUH", "KKJ", "TTJ", "UKB", "HSG", "NTQ", "HNA",
        "SYO", "YGJ", "KIJ", "TOY", "HAC", "SHI", "UKB"
    ]

    # 2. 英語名キーワードリスト (表記揺れ対応版)
    domestic_keywords = [
        # 主要空港
        "Haneda", "Narita", "Itami", "Kansai", "Chitose", "Fukuoka", "Naha", 
        "Nagoya", "Chubu", "Kobe",
        # 北海道・東北
        "Hakodate", "Asahikawa", "Obihiro", "Kushiro", "Kusiro", 
        "Memanbetsu", "Wakkanai", "Monbetsu", "Nakashibetsu", "Nakasibetsu",
        "Okushiri", "Okusiri", "Rishiri", "Risiri", "Rebun", 
        "Aomori", "Misawa", "Hanamaki", "Sendai", "Akita", "Yamagata", 
        "Shonai", "Syona", "Fukushima", "Hukushima",
        # 関東・甲信越
        "Ibaraki", "Oshima", "Osima", "Miyakejima", "Hachijojima", "Hachijo", 
        "Chofu", "Niigata", "Sado", "Toyama", "Noto", "Komatsu", 
        "Matsumoto", "Shizuoka", "Sizuoka",
        # 関西・中国・四国
        "Tottori", "Yonago", "Miho", "Izumo", "Iwami", "Oki", 
        "Okayama", "Hiroshima", "Ube", "Yamaguchi", "Iwakuni", 
        "Tokushima", "Tokusima", "Takamatsu", "Matsuyama", "Kochi", 
        "Nanki", "Shirahama", "Sirahama", "Tajima",
        # 九州・沖縄
        "Kitakyushu", "Saga", "Nagasaki", "Oita", "Kumamoto", "Miyazaki", 
        "Kagoshima", "Kagosima", "Amakusa", "Goto", "Fukue", "Tsushima", "Tusima",
        "Iki", "Tanegashima", "Yakushima", "Yakusima", 
        "Amami", "Tokunoshima", "Okinoerabu", "Yoron", 
        "Ishigaki", "Isigaki", "Miyako", "Shimojishima", "Shimoji", "Simoji",
        "Kumejima", "Tarama", "Yonaguni"
    ]

    # 判定1: T3なら即国際線
    if term == '3': return 250

    # 判定2: IATAコード一致
    if origin_val in domestic_codes: return 150

    # 判定3: キーワード一致
    for kw in domestic_keywords:
        if kw in origin_val:
            return 150
            
    # 上記に当てはまらなければ国際線
    return 250