from datetime import datetime, timedelta

def analyze_demand(flights):
    # 日本時間現在時刻
    now = datetime.utcnow() + timedelta(hours=9)
    
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
            
            # 【時差修正完了】 APIがJSTを返すため、+9時間は不要
            f_dt_jst = f_dt 
        except:
            continue

        # 【重複対策 / コードシェア排除】
        # 「便名」ではなく「到着時刻」と「出発地」で同一機体を判定
        dep = f.get('departure', {})
        # depがNoneの場合の対策
        if not dep: dep = {}
            
        origin_code = dep.get('iata') or dep.get('airport') or "UNK"
        
        # ユニークキー: "2026-01-26T01:05:00_SGN"
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
        
        # 【修正箇所: エラーの原因を修正】
        # api_handlerですでに文字列になっているため、辞書として扱わず、そのまま文字列として取得
        # None対策も含めて str() で囲む
        airline = str(f.get('airline', '')).lower()
        
        pax = f.get('pax_estimated', 0)
        
        if t_str == '3':
            terminal_counts["国際(T3)"] += pax
        elif t_str == '2':
            try: 
                # 便名から数字だけ抽出
                f_num_raw = str(f.get('flight_number', '0'))
                num = int(''.join(filter(str.isdigit, f_num_raw)))
            except: 
                num = 0
            
            if num % 2 == 0: terminal_counts["3号(T2)"] += pax
            else: terminal_counts["4号(T2)"] += pax
        elif t_str == '1':
            if 'japan airlines' in airline or 'jal' in airline: terminal_counts["2号(T1北)"] += pax
            else: terminal_counts["1号(T1南)"] += pax
        else:
            terminal_counts["国際(T3)"] += pax

    # -------------------------------------------------
    # 3. 未来予測テキスト
    # -------------------------------------------------
    forecast_data = {}
    for i in range(0, 3):
        target_h = (now.hour + i) % 24
        count = hourly_counts.get(target_h, 0)
        
        if count >= 1000: status = "🔥 高"
        elif count >= 300: status = "👀 通常"
        else: status = "📉 低"
        
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
    base_pax = 150
    term = flight.get('terminal')
    if term == '3':
        base_pax = 250
    return base_pax
