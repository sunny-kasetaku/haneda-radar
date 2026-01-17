from datetime import datetime, timedelta, timezone

def analyze_demand(flights):
    """
    重複排除 ＆ 時間窓フィルタリング（集計対象の厳選）
    """
    
    # 1. バケツの初期化
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    # 時間計算の基準
    now_utc = datetime.now(timezone.utc)
    now_jst = datetime.now()
    
    # ★ここが新機能：集計対象とする「時間窓」の設定
    # テスト用として「前後90分」の便だけを「現在の需要」としてカウントする
    # （本来の仕様：過去30分〜未来45分に近づけています）
    range_start = now_utc - timedelta(minutes=90)
    range_end = now_utc + timedelta(minutes=90)
    
    # 3時間予測用バケツ
    forecast = {
        "h1": {"label": (now_jst + timedelta(hours=1)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h2": {"label": (now_jst + timedelta(hours=2)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h3": {"label": (now_jst + timedelta(hours=3)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""}
    }

    seen_vessels = set()
    unique_flights = []

    for f in flights:
        # --- A. 重複排除 ---
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin', 'UNK')
        
        # 時刻(分まで)＋出発地で重複チェック
        vessel_key = f"{t_str[:16]}_{origin}"

        if vessel_key in seen_vessels:
            continue 

        seen_vessels.add(vessel_key)
        
        # --- B. 機材サイズ推計 ---
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        
        if '3' in term or 'I' in term:
            pax = 250 # 国際線
        elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "AMX", "ORC", "IBEX", "COMMUTER"]):
            pax = 50  # 小型
        else:
            pax = 150 # 標準

        f['pax_estimated'] = pax
        unique_flights.append(f)

        # --- C. 時間解析と振り分け ---
        try:
            flight_time = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
            
            # 【重要】現在の「メイン需要（上のカード）」に加算するかどうかの判定
            # 指定した「時間窓（前後90分）」に入っている便だけを足す！
            if range_start <= flight_time <= range_end:
                if '1' in term:
                    pax_t1 += pax
                elif '2' in term:
                    pax_t2 += pax
                else:
                    pax_t3 += pax

            # --- D. 3時間予測（未来判定）は別途計算 ---
            diff_hours = (flight_time - now_utc).total_seconds() / 3600

            if 0 <= diff_hours < 1:
                forecast["h1"]["pax"] += pax
            elif 1 <= diff_hours < 2:
                forecast["h2"]["pax"] += pax
            elif 2 <= diff_hours < 3:
                forecast["h3"]["pax"] += pax

        except:
            pass

    # 3. 予測ステータスの判定
    for k in ["h1", "h2", "h3"]:
        val = forecast[k]["pax"]
        if val >= 400:
            forecast[k]["status"] = "🚀 超高"
            forecast[k]["comment"] = "🔥 激アツ・第2波到来"
        elif val >= 200:
            forecast[k]["status"] = "⚠️ 中"
            forecast[k]["comment"] = "➡️ 需要継続中"
        else:
            forecast[k]["status"] = "👀 低"
            forecast[k]["comment"] = "⬇️ 撤収準備・待機"

    # 4. 最終結果
    # T1, T2は単純2等分
    return {
        "1号(T1南)": int(pax_t1 * 0.5),
        "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)":   int(pax_t2 * 0.5),
        "4号(T2)":   int(pax_t2 * 0.5),
        "国際(T3)":  pax_t3,
        "forecast": forecast,
        "unique_count": len(unique_flights),
        "flights": unique_flights
    }