# analyzer_v2.py
# ---------------------------------------------------------
# KASETACK Analyzer V2 (Data Processor)
# ---------------------------------------------------------
from datetime import datetime, timedelta

def analyze_demand(flights):
    """
    フライトデータを分析し、需要予測（pax計算・時間帯集計）を行う
    api_handler_v2 から受け取った「整形済みデータ」を処理する
    """
    
    # 1. バケツの初期化
    pax_t1 = 0
    pax_t2 = 0
    pax_t3 = 0
    
    # 現在時刻
    now = datetime.now()
    
    # 集計対象の時間窓（過去30分 〜 未来45分）
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
        # --- A. 重複排除キー作成 ---
        t_str = str(f.get('arrival_time', ''))
        origin = f.get('origin', 'UNK')
        
        # 同じ時間に同じ場所から来る便は重複とみなす
        vessel_key = f"{t_str[:16]}_{origin}"

        if vessel_key in seen_vessels:
            continue 
        seen_vessels.add(vessel_key)
        
        # --- B. 機材サイズ推計 ---
        # api_handlerで一旦150が入っているが、ここでターミナルや航空会社を見て精密化
        airline = str(f.get('airline', '')).upper()
        term = str(f.get('terminal', ''))
        
        pax = 150 # デフォルト
        if '3' in term or 'I' in term:
            pax = 250
        elif any(x in airline for x in ["WINGS", "J-AIR", "HAC", "AMX", "ORC", "IBEX", "COMMUTER"]):
            pax = 50

        # 計算した人数をデータに戻す（レンダラーで表示するため）
        f['pax_estimated'] = pax
        
        # --- C. 時間解析と振り分け ---
        try:
            # api_handler_v2 ですでに整形されているので、単純な日付変換でOK
            if 'T' in t_str:
                flight_time_str = t_str[:16] 
                flight_time = datetime.strptime(flight_time_str, "%Y-%m-%dT%H:%M")
            else:
                # フォーマットが違う場合はスキップ
                continue

            # 時間窓チェック (range_start <= flight <= range_end)
            if range_start <= flight_time <= range_end:
                unique_flights.append(f)
                
                if '1' in term:
                    pax_t1 += pax
                elif '2' in term:
                    pax_t2 += pax
                else:
                    pax_t3 += pax

            # --- D. 3時間予測（未来判定） ---
            diff_hours = (flight_time - now).total_seconds() / 3600

            if 0 <= diff_hours < 1:
                forecast["h1"]["pax"] += pax
            elif 1 <= diff_hours < 2:
                forecast["h2"]["pax"] += pax
            elif 2 <= diff_hours < 3:
                forecast["h3"]["pax"] += pax

        except Exception as e:
            # エラーデータはスキップ
            continue

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

    # 4. 最終結果を返す
    return {
        "1号(T1南)": int(pax_t1 * 0.5),
        "2号(T1北)": int(pax_t1 * 0.5),
        "3号(T2)":   int(pax_t2 * 0.5),
        "4号(T2)":   int(pax_t2 * 0.5),
        "国際(T3)":  pax_t3,
        "forecast": forecast,
        "unique_count": len(unique_flights),
        "flights": unique_flights,
        "update_time": now.strftime('%H:%M')
    }