from datetime import datetime, timedelta

def analyze_demand(flights, current_time=None):
    if current_time is None:
        now = datetime.utcnow() + timedelta(hours=9)
    else:
        now = current_time
    
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
        except: continue

        # api_handlerですでに 'origin_iata' というキーを作ってくれているので直接使う
        origin_code = f.get('origin_iata') or "UNK"
        
        unique_key = f"{dt_str}_{origin_code}"
        if unique_key in seen_flights: continue
        seen_flights.add(unique_key)

        if start_time <= f_dt_jst <= end_time:
            pax = estimate_pax(f)
            f['pax_estimated'] = pax
            filtered_flights.append(f)

        h = f_dt_jst.hour
        pax = estimate_pax(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax

    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # --- 2. ターミナル判定 & タグ付け ---
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        raw_t_str = str(f.get('terminal', ''))
        airline = str(f.get('airline', '')).lower()
        pax = f.get('pax_estimated', 0)
        
        target_terminal = "3" # デフォルト

        # 航空会社による判定
        if 'all nippon' in airline or 'ana' in airline or 'air do' in airline or 'solaseed' in airline:
            target_terminal = "2"
        elif 'japan airlines' in airline or 'jal' in airline or 'skymark' in airline or 'starflyer' in airline:
            target_terminal = "1"
        elif raw_t_str in ['1', '2', '3']:
            target_terminal = raw_t_str
        elif pax <= 200:
            target_terminal = "1"

        # バケツ振り分け & タグ付け
        if target_terminal == "3":
            terminal_counts["国際(T3)"] += pax
            f['exit_type'] = "国際(T3)"
            
        elif target_terminal == "2":
            try: 
                f_num_raw = str(f.get('flight_number', '0'))
                num = int(''.join(filter(str.isdigit, f_num_raw)))
            except: num = 0
            
            if num % 2 == 0: 
                terminal_counts["3号(T2)"] += pax
                f['exit_type'] = "3号(T2)"
            else: 
                terminal_counts["4号(T2)"] += pax
                f['exit_type'] = "4号(T2)"
            
        elif target_terminal == "1":
            if 'japan airlines' in airline or 'jal' in airline: 
                terminal_counts["2号(T1北)"] += pax
                f['exit_type'] = "2号(T1北)"
            else: 
                terminal_counts["1号(T1南)"] += pax
                f['exit_type'] = "1号(T1南)"

    # --- 3. 未来予測 ---
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
    乗客数推定ロジック (サニーさんリスト完全維持版)
    """
    term = str(flight.get('terminal', ''))
    
    origin_val = flight.get('origin_iata', '')
    origin_name = flight.get('origin', '')

    # 検索漏れを防ぐため、コードと名前を結合して小文字化チェック用文字列を作る
    check_str = (str(origin_val) + " " + str(origin_name)).lower()

    # --- 1. API機材情報チェック (最優先) ---
    aircraft = str(flight.get('aircraft', '')).lower()
    if aircraft and aircraft != 'none':
        if any(x in aircraft for x in ['777', '789', '781', '350', '330', '747', '380']):
            return 350 if term == '3' else 300
        if any(x in aircraft for x in ['737', '320', '321', 'e19', '738', '73h']):
            return 150

    # --- 2. 出身地によるサイズ推測 ---
    
    # 長距離国際線 -> 350
    long_haul_keys = ["jfk", "lax", "sfo", "sea", "lhr", "cdg", "fra", "hel", "dxb", "doh", "ist", "hnl", "yvr", "syd", "mel"]
    if any(k in check_str for k in long_haul_keys): return 350
    
    # 国内幹線 (札幌、福岡、那覇、伊丹) -> 300
    major_keys = ["cts", "fuk", "oka", "itm", "sapporo", "fukuoka", "naha", "okinawa", "itami", "osaka", "新千歳", "福岡", "那覇", "伊丹", "大阪"]
    if any(k in check_str for k in major_keys): return 300

    # --- 3. その他国内線 (150人) ---
    
    # リストA: サニーさんの国内コードリスト (そのまま維持)
    domestic_codes = [
        "CTS", "FUK", "OKA", "ITM", "KIX", "NGO", "KMQ", "HKD", "HIJ", "MYJ",
        "KCZ", "TAK", "KMJ", "KMI", "KOJ", "ISG", "MMY", "IWK", "UBJ", "TKS",
        "AOJ", "MSJ", "OIT", "AXT", "GAJ", "OKJ", "NGS", "AKJ", "OBO", "SHM",
        "ASJ", "MMB", "IZO", "KUH", "KKJ", "TTJ", "UKB", "HSG", "NTQ", "HNA",
        "SYO", "YGJ", "KIJ", "TOY", "HAC", "SHI", "UKB"
    ]

    # リストB: サニーさんの国内キーワードリスト (そのまま維持)
    domestic_keywords = [
        "Haneda", "Narita", "Itami", "Kansai", "Chitose", "Fukuoka", "Naha", 
        "Nagoya", "Chubu", "Kobe",
        "Hakodate", "Asahikawa", "Obihiro", "Kushiro", "Kusiro", 
        "Memanbetsu", "Wakkanai", "Monbetsu", "Nakashibetsu", "Nakasibetsu",
        "Okushiri", "Okusiri", "Rishiri", "Risiri", "Rebun", 
        "Aomori", "Misawa", "Hanamaki", "Sendai", "Akita", "Yamagata", "Junmachi",
        "Shonai", "Syona", "Fukushima", "Hukushima", "Odate", "Noshiro",
        "Ibaraki", "Oshima", "Osima", "Miyakejima", "Hachijojima", "Hachijo", 
        "Chofu", "Niigata", "Sado", "Toyama", "Noto", "Komatsu", 
        "Matsumoto", "Shizuoka", "Sizuoka",
        "Tottori", "Yonago", "Miho", "Izumo", "Iwami", "Oki", 
        "Okayama", "Hiroshima", "Ube", "Yamaguchi", "Iwakuni", 
        "Tokushima", "Tokusima", "Takamatsu", "Matsuyama", "Kochi", 
        "Nanki", "Shirahama", "Sirahama", "Tajima",
        "Kitakyushu", "Saga", "Nagasaki", "Oita", "Kumamoto", "Miyazaki", 
        "Kagoshima", "Kagosima", "Amakusa", "Goto", "Fukue", "Tsushima", "Tusima",
        "Iki", "Tanegashima", "Yakushima", "Yakusima", 
        "Amami", "Tokunoshima", "Okinoerabu", "Yoron", 
        "Ishigaki", "Isigaki", "Miyako", "Shimojishima", "Shimoji", "Simoji",
        "Kumejima", "Tarama", "Yonaguni"
    ]
    
    # リストC: 追加日本語リスト (ここが重要！)
    domestic_japanese = [
        "神戸", "函館", "旭川", "帯広", "釧路", "女満別", "稚内", "青森", "三沢", "花巻", "仙台", "秋田", "山形", "庄内",
        "福島", "茨城", "新潟", "富山", "小松", "静岡", "鳥取", "米子", "出雲", "岡山", "広島", "山口", "徳島", "高松",
        "松山", "高知", "南紀白浜", "北九州", "佐賀", "長崎", "大分", "熊本", "宮崎", "鹿児島", "石垣", "宮古",
        "関空", "関西", "中部", "名古屋"
    ]

    # リストAチェック (コード)
    if origin_val in domestic_codes: return 150
    
    # リストBチェック (英語キーワード - 小文字にして部分一致検索)
    for kw in domestic_keywords:
        if kw.lower() in check_str: return 150
        
    # リストCチェック (日本語キーワード)
    for kw in domestic_japanese:
        if kw in check_str: return 150

    # デフォルト
    return 250 if term == '3' else 150