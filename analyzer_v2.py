from datetime import datetime, timedelta

def analyze_demand(flights):
    # 日本時間現在時刻
    now = datetime.utcnow() + timedelta(hours=9)
    
    # -------------------------------------------------
    # 1. 時間枠ごとの集計 & 表示フィルター
    # -------------------------------------------------
    
    # 【最終決定設定】
    # 過去: 60分 (T3の入国審査・荷物待ち時間をフルカバー。乗り場にいる客を逃さない)
    # 未来: 30分 (アプローチ時間を考慮しつつ、長時間待ちの「罠」を避ける絶妙なライン)
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
            # 時刻パース (YYYY-MM-DDTHH:MM:SS)
            # 文字列の長さを調整してパースエラーを防ぐ
            dt_str = arr_time_str[:19] 
            f_dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
            
            # UTC -> JST変換 (+9時間)
            f_dt_jst = f_dt + timedelta(hours=9)
        except:
            continue

        # 重複排除 (同じ便名がactiveとscheduledで重複した場合など)
        flight_id = f"{f.get('flight_number')}_{f_dt_jst.day}"
        if flight_id in seen_flights:
            continue
        seen_flights.add(flight_id)

        # -----------------------------------------------------------
        # 1. リアルタイムリストへの振り分け
        # -----------------------------------------------------------
        # 設定した「過去60分〜未来30分」の範囲にある便だけを表示
        if start_time <= f_dt_jst <= end_time:
            pax = estimate_pax(f)
            f['pax_estimated'] = pax
            filtered_flights.append(f)

        # -----------------------------------------------------------
        # 2. 未来予測用の集計 (時間帯別)
        # -----------------------------------------------------------
        # ここは「傾向」を見るためのものなので、フィルターせず全データを集計
        h = f_dt_jst.hour
        pax = estimate_pax(f)
        hourly_counts[h] = hourly_counts.get(h, 0) + pax

    # 到着時間順にソートして見やすくする
    filtered_flights.sort(key=lambda x: x.get('arrival_time'))

    # -------------------------------------------------
    # 2. ターミナル別集計 (円グラフ/分布用)
    # -------------------------------------------------
    terminal_counts = {
        "1号(T1南)": 0, "2号(T1北)": 0,
        "3号(T2)": 0, "4号(T2)": 0,
        "国際(T3)": 0
    }
    
    for f in filtered_flights:
        t_str = str(f.get('terminal', ''))
        airline = f.get('airline', '').lower()
        pax = f.get('pax_estimated', 0)
        
        # ターミナル判定ロジック
        if t_str == '3':
            terminal_counts["国際(T3)"] += pax
        elif t_str == '2':
            # T2 (便名の偶数/奇数で3号・4号を仮振り分け)
            try: num = int(''.join(filter(str.isdigit, f.get('flight_number', '0'))))
            except: num = 0
            if num % 2 == 0: terminal_counts["3号(T2)"] += pax
            else: terminal_counts["4号(T2)"] += pax
        elif t_str == '1':
            # T1 (JAL=北/2号, その他=南/1号)
            if 'japan airlines' in airline or 'jal' in airline: terminal_counts["2号(T1北)"] += pax
            else: terminal_counts["1号(T1南)"] += pax
        else:
            # 不明な場合はT3へ (国際線の可能性が高いため)
            terminal_counts["国際(T3)"] += pax

    # -------------------------------------------------
    # 3. 未来予測テキストの生成
    # -------------------------------------------------
    forecast_data = {}
    # 現在(0時間後)〜2時間後までの3枠を作成
    for i in range(0, 3):
        target_h = (now.hour + i) % 24
        count = hourly_counts.get(target_h, 0)
        
        # 混雑度判定
        if count >= 1000: status = "🔥 高"
        elif count >= 300: status = "👀 通常"
        else: status = "📉 低"
        
        # コメント判定
        if count >= 1000: comment = "確変中"
        elif count >= 300: comment = "需要あり"
        else: comment = "静か"

        key = f"h{i+1}"
        forecast_data[key] = {
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
    乗客数の推計ロジック
    """
    base_pax = 150 # 国内線・小型機のベース
    term = flight.get('terminal')
    
    # 国際線(T3)は大型機が多く、客単価も高いため重要視する
    if term == '3':
        base_pax = 250
        
    return base_pax
