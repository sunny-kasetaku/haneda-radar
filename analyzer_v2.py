from datetime import datetime, timedelta

def analyze_demand(flights):
    """
    重複排除 ＆ 実戦的時間窓フィルタリング（-30分 〜 +45分）
    【修正】入力データを「UTC」とみなして+9時間する処理を廃止。
           APIの数字をそのまま「日本時間」として扱い、現在時刻と比較する。
    """
    
    # 1. バケツの初期化
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    # 時間計算の基準（JST同士で比較するため、timezone.utcを使わずネイティブな日時で比較）
    now = datetime.now()
    
    # ★実戦仕様：集計対象の時間窓設定
    # 過去30分 〜 未来45分
    range_start = now - timedelta(minutes=30)
    range_end = now + timedelta(minutes=45)
    
    # 3時間予測用バケツ
    forecast = {
        "h1": {"label": (now + timedelta(hours=1)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h2": {"label": (now + timedelta(hours=2)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""},
        "h3": {"label": (now + timedelta(hours=3)).strftime("%H:00〜"), "pax": 0, "status": "", "comment": ""}
    }

    seen_vessels = set()
    unique_flights = []

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
            # 【修正箇所】
            # 以前: datetime.fromisoformat(t_str.replace('Z', '+00:00')) -> UTC扱い
            # 今回: 単純に文字列から日時を復元し、そのまま比較する（APIはJSTを返している前提）
            if 'T' in t_str:
                flight_time_str = t_str[:16] # "2023-10-27T16:55" までを取得
                flight_time = datetime.strptime(flight_time_str, "%Y-%m-%dT%H:%M")
            else:
                continue

            # 【重要】時間窓チェック (-30分 〜 +45分)
            # flight_time(16:55) vs now(01:40) -> 範囲外！ -> 消える（正しい挙動）
            # もし本番で flight_time(01:40) が来れば -> 範囲内！ -> 表示される
            if range_start <= flight_time <= range_end:
                unique_flights.append(f)
                
                if '1' in term:
                    pax_t1 += pax
                elif '2' in term:
                    pax_t2 += pax
                else:
                    pax_t3 += pax

            # --- D. 3時間予測（未来判定） ---
            # 差分（時間）を計算
            diff_hours = (flight_time - now).total_seconds() / 3600

            if 0 <= diff_hours < 1:
                forecast["h1"]["pax"] += pax
            elif 1 <= diff_hours < 2:
                forecast["h2"]["pax"] += pax
            elif 2 <= diff_hours < 3:
                forecast["h3"]["pax"] += pax

        except Exception as e:
            # 日付解析エラー等の場合はスキップ
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
        "flights": unique_flights
    }