from datetime import datetime, timedelta

# --- グローバル定義: リストをここに移動して共通化 ---

# 1. 国内線コード (これ以外は国際線とみなす)
DOMESTIC_CODES = [
    "CTS", "FUK", "OKA", "ITM", "KIX", "NGO", "KMQ", "HKD", "HIJ", "MYJ",
    "KCZ", "TAK", "KMJ", "KMI", "KOJ", "ISG", "MMY", "IWK", "UBJ", "TKS",
    "AOJ", "MSJ", "OIT", "AXT", "GAJ", "OKJ", "NGS", "AKJ", "OBO", "SHM",
    "ASJ", "MMB", "IZO", "KUH", "KKJ", "TTJ", "UKB", "HSG", "NTQ", "HNA",
    "SYO", "YGJ", "KIJ", "TOY", "HAC", "SHI", "UKB"
]

# 2. 国内線キーワード (英語)
DOMESTIC_KEYWORDS = [
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

# 3. 国内線キーワード (日本語)
DOMESTIC_JAPANESE = [
    "神戸", "函館", "旭川", "帯広", "釧路", "女満別", "稚内", "青森", "三沢", "花巻", "仙台", "秋田", "山形", "庄内",
    "福島", "茨城", "新潟", "富山", "小松", "静岡", "鳥取", "米子", "出雲", "岡山", "広島", "山口", "徳島", "高松",
    "松山", "高知", "南紀白浜", "北九州", "佐賀", "長崎", "大分", "熊本", "宮崎", "鹿児島", "石垣", "宮古",
    "関空", "関西", "中部", "名古屋", "福岡", "那覇", "伊丹", "新千歳", "大阪", "札幌"
]

# 4. JAL南ウイング行き先リスト (中国・四国・九州・沖縄)
# これに含まれない国内線は「北ウイング」と判定します
JAL_SOUTH_ORIGINS = [
    "HIJ", "UBJ", "IWK", "TKS", "TAK", "MYJ", "KCZ", "FUK", "KKJ", "HSG", "NGS", "OIT", "KMJ", "KMI", "KOJ", 
    "ASJ", "OKA", "ISG", "MMY", "OKJ", "IZO", "OKI",
    "Hiroshima", "Yamaguchi", "Ube", "Iwakuni", "Tokushima", "Takamatsu", "Matsuyama", "Kochi",
    "Fukuoka", "Kitakyushu", "Saga", "Nagasaki", "Oita", "Kumamoto", "Miyazaki", "Kagoshima",
    "Amami", "Naha", "Okinawa", "Ishigaki", "Miyako", "Okayama", "Izumo",
    "広島", "山口", "宇部", "岩国", "徳島", "高松", "松山", "高知",
    "福岡", "北九州", "佐賀", "長崎", "大分", "熊本", "宮崎", "鹿児島",
    "奄美", "那覇", "沖縄", "石垣", "宮古", "岡山", "出雲"
]

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

        origin_code = f.get('origin_iata') or "UNK"
        origin_name = f.get('origin') or ""
        
        unique_key = f"{dt_str}_{origin_code}"
        if unique_key in seen_flights: continue
        seen_flights.add(unique_key)

        if start_time <= f_dt_jst <= end_time:
            # 優先度1: estimate_pax で国内/国際判定も含めて計算
            pax, is_domestic = estimate_pax_and_type(f)
            f['pax_estimated'] = pax
            f['is_domestic'] = is_domestic # 判定結果を保存
            filtered_flights.append(f)

        h = f_dt_jst.hour
        pax, _ = estimate_pax_and_type(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax

    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # --- 2. ターミナル判定 & タグ付け (修正版) ---
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        raw_t_str = str(f.get('terminal', ''))
        airline = str(f.get('airline', '')).lower()
        pax = f.get('pax_estimated', 0)
        is_domestic = f.get('is_domestic', True)
        
        origin_code = f.get('origin_iata') or ""
        origin_name = f.get('origin') or ""
        check_str = (str(origin_code) + " " + str(origin_name)).lower()
        
        target_terminal = "3" # デフォルト

        # 【ロジック修正】
        # 1. 国際線判定 (出身地リストにない場合は強制T3)
        if not is_domestic:
            target_terminal = "3"
        
        # 2. APIの明示的な値を尊重 (ただし国際線判定されたらT3優先)
        elif raw_t_str in ['1', '2', '3']:
            target_terminal = raw_t_str
            
        # 3. 航空会社による判定 (国内線の場合のみ)
        elif 'all nippon' in airline or 'ana' in airline or 'air do' in airline or 'solaseed' in airline:
            target_terminal = "2"
        elif 'japan airlines' in airline or 'jal' in airline or 'skymark' in airline or 'starflyer' in airline:
            target_terminal = "1"
        else:
            # 国内線だが航空会社不明 -> 人数で推定 (200以下ならT1系と仮定)
            target_terminal = "1" if pax <= 200 else "2"

        # バケツ振り分け & タグ付け
        if target_terminal == "3":
            terminal_counts["国際(T3)"] += pax
            f['exit_type'] = "国際(T3)"
            
        elif target_terminal == "2":
            # ANA系 (T2) の偶数/奇数判定
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
            # JAL系 (T1) の北/南判定
            # デフォルトは北 (2号)
            wing = "北"
            
            # スターフライヤー(関西・山口宇部)、スカイマーク -> 北
            # JAL -> 行き先で分岐
            if 'japan airlines' in airline or 'jal' in airline:
                # JAL南ウイング判定 (中国・四国・九州・沖縄)
                is_south = False
                for k in JAL_SOUTH_ORIGINS:
                    if k in origin_code or k.lower() in check_str:
                        is_south = True
                        break
                
                if is_south:
                    wing = "南"
                else:
                    wing = "北"
            
            # スターフライヤーの北九州・福岡は南 (T1南) だが今回はJAL優先で簡易化
            
            if wing == "北": 
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

def estimate_pax_and_type(flight):
    """
    乗客数と国内線/国際線フラグを返す
    Returns: (pax, is_domestic)
    """
    term = str(flight.get('terminal', ''))
    origin_val = flight.get('origin_iata', '')
    origin_name = flight.get('origin', '')
    check_str = (str(origin_val) + " " + str(origin_name)).lower()
    
    # 1. 国内線判定
    is_domestic = False
    
    if origin_val in DOMESTIC_CODES: is_domestic = True
    else:
        for kw in DOMESTIC_KEYWORDS:
            if kw.lower() in check_str: 
                is_domestic = True; break
        if not is_domestic:
            for kw in DOMESTIC_JAPANESE:
                if kw in check_str:
                    is_domestic = True; break
    
    # 2. 機材判定 (最優先)
    aircraft = str(flight.get('aircraft', '')).lower()
    if aircraft and aircraft != 'none':
        # 大型機
        if any(x in aircraft for x in ['777', '789', '781', '350', '330', '747', '380']):
            return (350 if not is_domestic else 300), is_domestic
        # 小型機
        if any(x in aircraft for x in ['737', '320', '321', 'e19', '738', '73h']):
            return 150, is_domestic

    # 3. エリア別サイズ推測
    
    # 国際線 (リストにない) -> 350(長距離) or 250(近距離)
    if not is_domestic:
        # 長距離リスト (簡易)
        long_haul = ["jfk", "lax", "sfo", "sea", "lhr", "cdg", "fra", "hel", "dxb", "doh", "ist", "hnl", "yvr", "syd", "mel"]
        if any(k in check_str for k in long_haul): 
            return 350, False
        return 250, False # 北京・上海などはここ

    # 国内線
    major_keys = ["cts", "fuk", "oka", "itm", "sapporo", "fukuoka", "naha", "itami", "新千歳", "福岡", "那覇", "伊丹", "大阪"]
    if any(k in check_str for k in major_keys): 
        return 300, True

    return 150, True