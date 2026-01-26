from datetime import datetime, timedelta

# 【修正点】current_time引数を追加
def analyze_demand(flights, current_time=None):
    # 日本時間現在時刻
    # 引数で渡されなかった場合の保険
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
    
    # 重複排除用のセット (コードシェア対策)
    seen_flights = set()

    for f in flights:
        arr_time_str = f.get('arrival_time', '')
        if not arr_time_str: continue
        
        try:
            # 時刻パース
            dt_str = arr_time_str[:19] 
            f_dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            
            # APIがJST（日本時間）を返している前提。UTCの場合はここで調整が必要。
            f_dt_jst = f_dt 
        except:
            continue

        # 【重複対策 / コードシェア排除】
        dep = f.get('departure', {})
        if not dep: dep = {}
        origin_code = dep.get('iata') or dep.get('airport') or "UNK"
        f['origin_iata'] = origin_code # estimate_paxで使うために保存
        
        # ユニークキー: "時刻_出発地" で同一機体を判定
        unique_key = f"{dt_str}_{origin_code}"

        if unique_key in seen_flights:
            continue
        seen_flights.add(unique_key)

        # -----------------------------------------------------------
        # 1. リアルタイムリストへの振り分け
        # -----------------------------------------------------------
        if start_time <= f_dt_jst <= end_time:
            pax = estimate_pax(f)
            f['pax_estimated'] = pax
            filtered_flights.append(f)

        # -----------------------------------------------------------
        # 2. 未来予測用の集計
        # -----------------------------------------------------------
        # 未来の便だけを集計するように判定を追加しても良いですが、
        # ここはサニーさんのロジック通り「全データから時間帯集計」を行います
        h = f_dt_jst.hour
        pax = estimate_pax(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax

    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # -------------------------------------------------
    # 2. ターミナル別集計
    # -------------------------------------------------
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        t_str = str(f.get('terminal', ''))
        airline = str(f.get('airline', '')).lower()
        pax = f.get('pax_estimated', 0)
        
        # --- 判定ロジックの修正点 ---
        # T3(国際線専用) または 「人数が250人(国際線判定済み)」の場合は国際線として集計
        if t_str == '3' or pax >= 250:
            terminal_counts["国際(T3)"] += pax
            
        elif t_str == '2':
            # 第2ターミナル(T2)に到着する国内線(ANA等)の振り分け
            try: 
                f_num_raw = str(f.get('flight_number', '0'))
                num = int(''.join(filter(str.isdigit, f_num_raw)))
            except: 
                num = 0
            
            if num % 2 == 0: terminal_counts["3号(T2)"] += pax
            else: terminal_counts["4号(T2)"] += pax
            
        elif t_str == '1':
            # 第1ターミナル(T1)の振り分け (JALは北、それ以外は南)
            if 'japan airlines' in airline or 'jal' in airline: 
                terminal_counts["2号(T1北)"] += pax
            else: 
                terminal_counts["1号(T1南)"] += pax
        else:
            # ターミナル不明な場合も、国際線としてカウント（安全側）
            terminal_counts["国際(T3)"] += pax

    # -------------------------------------------------
    # 3. 未来予測データ作成
    # -------------------------------------------------
    forecast_data = {}
    for i in range(0, 3):
        # nowを基準にするよう修正（以前はdatetime.utcnowそのままでズレていた可能性があります）
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
    第3ターミナル(T3)または出発地が「3文字の空港コード」かつ特定の国内空港以外なら国際線とみなす。
    """
    term = str(flight.get('terminal', ''))
    origin_iata = flight.get('origin_iata', '')
    
    # 日本の主要国内線空港コードリスト
    domestic_airports = [
        "CTS", "FUK", "OKA", "ITM", "KIX", "NGO", "KMQ", "HKD", "HIJ", "MYJ",
        "KCZ", "TAK", "KMJ", "KMI", "KOJ", "ISG", "MMY", "IWK", "UBJ", "TKS",
        "AOJ", "MSJ", "OIT", "AXT", "GAJ", "OKJ", "NGS", "AKJ", "OBO", "SHM",
        "ASJ", "MMB", "IZO", "KUH", "KKJ", "TTJ", "UKB", "HSG", "NTQ", "HNA",
        "SYO", "YGJ", "KIJ", "TOY", "HAC", "SHI"
    ]

    # 国際線の判定条件：
    # 1. ターミナルが3(T3)である
    # 2. または、出発地(IATA)が上記国内リストに含まれていない
    if term == '3' or (origin_iata and origin_iata not in domestic_airports):
        return 250  # 国際線推定
    
    return 150  # 国内線推定