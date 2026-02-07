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

# 🦁【追加】ANA(T2)で確実に「3号」に入れるべき西日本エリアリスト (4号誤爆防止)
# ※ここを修正しました（鳥取・山陰・北陸を追加）
ANA_WEST_FORCE_3 = [
    "FUK", "KOJ", "KMJ", "NGS", "OIT", "KMI", "HIJ", "UBJ", "IWK", "MYJ", "KCZ", "TAK", "TKS", "OKJ", "OKA", "ISG", "MMY", "UKB", "KIX", "ITM",
    "FUKUOKA", "KAGOSHIMA", "KUMAMOTO", "NAGASAKI", "OITA", "MIYAZAKI", "HIROSHIMA", "YAMAGUCHI", "IWAKUNI", "MATSUYAMA", "KOCHI", "TAKAMATSU", "TOKUSHIMA", "OKAYAMA", "OKINAWA", "NAHA", "ISHIGAKI", "MIYAKO", "KOBE", "KANSAI", "ITAMI", "OSAKA",
    "福岡", "鹿児島", "熊本", "長崎", "大分", "宮崎", "広島", "山口", "岩国", "松山", "高知", "高松", "徳島", "岡山", "沖縄", "那覇", "石垣", "宮古", "神戸", "関西", "伊丹", "大阪",
    # 🦁 追加: 山陰・北陸エリア
    "TTJ", "YGJ", "IWJ", "NTQ", "TOY", "KMQ",
    "TOTTORI", "YONAGO", "IWAMI", "NOTO", "TOYAMA", "KOMATSU",
    "鳥取", "米子", "石見", "能登", "富山", "小松"
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

    for f in filtered_flights:
        # 重複排除用のキー
        # 同じ便名・同じ時間ならスキップするが、コードシェアの場合は便名が違うので
        # 「到着時間 + 出発地」でユニーク判定をするのが安全
        pass 

    for f in flights:
        arr_time_str = f.get('arrival_time', '')
        if not arr_time_str: continue
        try:
            dt_str = arr_time_str[:19] 
            f_dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            f_dt_jst = f_dt 
        except: continue

        origin_code = f.get('origin_iata') or "UNK"
        # ユニークキー: 時間_出発地 (便名はコードシェアで変わるため含めない方が安全だが、今回は便名も含める)
        # ただし、同じ機材で複数の便名がついている場合(JL5012 / GA874)、APIは別々のレコードとして送ってくることが多い。
        # これを統合するのは難しいので、今回は「別々の便」として扱われてしまうのは許容しつつ、
        # 確実に「国際線」として拾うことを優先する。
        
        unique_key = f"{dt_str}_{f.get('flight_number')}"
        if unique_key in seen_flights: continue
        seen_flights.add(unique_key)

        # 【変更点】ここだけ変えました。時間を絞らず、全データを通します。
        # if start_time <= f_dt_jst <= end_time:
        if True:
            # 優先度1: estimate_pax で国内/国際判定も含めて計算
            pax, is_domestic = estimate_pax_and_type(f)
            
            # 🦁【追加】APIハンドラーのpaxを尊重
            if f.get('pax') and f.get('pax') > 150:
                pax = f.get('pax')
                
            f['pax_estimated'] = pax
            f['is_domestic'] = is_domestic # 判定結果を保存
            filtered_flights.append(f)

        # 時間帯別集計用 (フィルタリング前の全データから推計)
        # ただし、直近のものだけを集計しないと意味がないので、ここもフィルタリング後に回しても良いが
        # 元のロジックを尊重して「当日全データ」から集計するならここ。
        # 今回は「表示範囲内」の集計だけでよければ下でやるべきだが、
        # "今後の需要予測" は未来のデータ全てを見たいので、別ループにするか、ここでやるか。
        # → ここでやると「範囲外」の未来データも拾えるのでOK。
        h = f_dt_jst.hour
        pax_forecast, _ = estimate_pax_and_type(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax_forecast

    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # --- 2. ターミナル判定 & タグ付け (修正版) ---
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        # 🦁【追加ロジック】APIハンドラーの決定を絶対遵守し、西日本便を3号へ補正する
        pre_determined_exit = f.get('exit_type')
        pax = f.get('pax_estimated', 0)

        # 1. 西日本便の強制3号補正 (4号判定されていた場合の救済)
        if str(f.get('terminal')) == "2":
            check_str = (str(f.get('origin_iata', '')) + str(f.get('origin', ''))).upper()
            is_west = False
            for kw in ANA_WEST_FORCE_3:
                if kw in check_str:
                    is_west = True
                    break
            
            if is_west:
                pre_determined_exit = "3号(T2)"
                f['exit_type'] = "3号(T2)"

        # 🦁【さらに追加】ANAスターフライヤー便(3800番台)の正確な1号振り分け
        # APIが「1」と言っているが、ANA名義なので独自判定で「2号(T1北)」にされがちなものを救済
        try:
            fn_str = str(f.get('flight_number', '0'))
            fn_num = int(''.join(filter(str.isdigit, fn_str)))
            # ANA便名で3800番台はSFJ運航 (T1発着)
            if 'ANA' in str(f.get('airline', '')).upper() and 3800 <= fn_num <= 3899:
                # SFJの南/北判定
                # 南: 北九州(KKJ), 福岡(FUK), 那覇(OKA), 中部(NGO)
                # 北: 関空(KIX), 山口宇部(UBJ)
                check_sfj = (str(f.get('origin_iata', '')) + str(f.get('origin', ''))).upper()
                if any(x in check_sfj for x in ["KKJ", "FUK", "OKA", "NGO", "北九州", "福岡", "那覇", "中部"]):
                    pre_determined_exit = "1号(T1南)"
                    f['exit_type'] = "1号(T1南)"
                else:
                    pre_determined_exit = "2号(T1北)"
                    f['exit_type'] = "2号(T1北)"
        except:
            pass

        # 2. 決定済みの場合はカウントして、下の独自判定ロジックをスキップ(continue)する
        if pre_determined_exit and pre_determined_exit in terminal_counts:
            terminal_counts[pre_determined_exit] += pax
            continue
        # 🦁【追加終わり】既存コードは以下そのまま温存

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
    
    # 1. 国内線判定 (厳密化)
    is_domestic = False
    
    # 明確な国内空港コード
    if origin_val in DOMESTIC_CODES: 
        is_domestic = True
    else:
        # キーワード検索
        for kw in DOMESTIC_KEYWORDS:
            if kw.lower() in check_str: 
                is_domestic = True; break
        
        # 日本語キーワード検索
        if not is_domestic:
            for kw in DOMESTIC_JAPANESE:
                if kw in check_str:
                    is_domestic = True; break
    
    # 【追加】国際線コードの明示的チェック (誤判定防止)
    # ジャカルタ(CGK/Jakarta), シンガポール(SIN/Singapore), ロンドン(LHR/London), ソウル(GMP/SEL/Seoul)
    # これらが含まれていたら、上記でDomestic判定されていても強制的にFalseにする
    INTERNATIONAL_KEYWORDS = [
        "jakarta", "cgk", "singapore", "sin", "london", "lhr", "seoul", "gmp", "icn", 
        "bangkok", "bkk", "taipei", "tpe", "tsa", "shanghai", "pvg", "sha", "hong kong", "hkg",
        "paris", "cdg", "frankfurt", "fra", "los angeles", "lax", "new york", "jfk", "honolulu", "hnl"
    ]
    for kw in INTERNATIONAL_KEYWORDS:
        if kw in check_str:
            is_domestic = False
            break

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