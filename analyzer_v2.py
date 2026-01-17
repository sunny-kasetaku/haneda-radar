from datetime import datetime, timedelta, timezone

def analyze_demand(flights):
    """
    重複排除 ＆ 時間窓フィルタリング（完全整合性版）
    リストに「計算に使った便」だけを残すことで、レンダラー側の合計と一致させる。
    """
    
    # 1. バケツの初期化
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    # 時間計算の基準
    now_utc = datetime.now(timezone.utc)
    now_jst = datetime.now()
    
    # 時間窓の設定（前後90分）
    # この期間の便だけを「現在の需要」としてカウントし、リストにも残す
    range_start = now_utc - timedelta(minutes=90)
    range_end = now_utc + timedelta(minutes=90)
    
    # 3時間予測用バケツ
    forecast = {
        "h1": {"label": (now_jst + timedelta(hours=1)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h2": {"label": (now_jst + timedelta(hours=2)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h3": {"label": (now_jst + timedelta(hours=3)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""}
    }

    seen_vessels = set()
    unique_flights = [] # ここには「時間窓内」の便だけを入れる

    for f in flights:
        # --- A. 重複排除 ---
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin', 'UNK')
        vessel_key = f"{t_str[:16]}_{origin}"

        if vessel_key in seen_vessels:
            continue 
        seen_vessels.add(vessel_key)
        
        # --- B. 機材サイズ推計 ---
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        
        if '3' in term or 'I' in term:
            pax = 250
        elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "AMX", "ORC", "IBEX", "COMMUTER"]):
            pax = 50
        else:
            pax = 150

        f['pax_estimated'] = pax
        
        # --- C. 時間解析と厳密な振り分け ---
        try:
            flight_time = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
            
            # 【重要】時間窓チェック
            if range_start <= flight_time <= range_end:
                # 範囲内なら「今の客」としてカウント ＆ リストに追加
                unique_flights.append(f)
                
                if '1' in term:
                    pax_t1 += pax
                elif '2' in term:
                    pax_t2 += pax
                else:
                    pax_t3 += pax

            # --- D. 3時間予測（未来判定） ---
            # ※予測は「範囲外の未来」も含めて計算する必要があるため、flight_timeから直接判定
            diff_hours = (flight_time - now_utc).total_seconds() / 3600

            if 0 <= diff_hours < 1:
                forecast["h1"]["pax"] += pax
            elif 1 <= diff_hours < 2:
                forecast["h2"]["pax"] += pax
            elif 2 <= diff_hours < 3:
                forecast["h3"]["pax"] += pax

        except:
            pass

    # 3. 予測ステータス判定
    for k in ["h1", "h2", "h3"]:
        val = forecast[k]["pax"]
        if val >= 400:
            forecast[k]["status"] = "🚀 超高"
            forecast[k]["comment"] = "🔥 激アツ・第2波"
        elif val >= 200:
            forecast[k]["status"] = "⚠️ 中"
            forecast[k]["comment"] = "➡️ 需要継続"
        else:
            forecast[k]["status"] = "👀 低"
            forecast[k]["comment"] = "⬇️ 撤収準備"

    # 4. 最終結果
    return {
        "1号(T1南)": int(pax_t1 * 0.5),
        "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)":   int(pax_t2 * 0.5),
        "4号(T2)":   int(pax_t2 * 0.5),
        "国際(T3)":  pax_t3,
        "forecast": forecast,
        "unique_count": len(unique_flights),
        "flights": unique_flights # 厳選されたリスト
    }