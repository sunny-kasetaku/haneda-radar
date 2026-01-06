# (中略: STATS_CONFIGなどは維持)

# 🌟 出身地による1号/2号の判定キーワード
SOUTH_CITIES = ["福岡", "那覇", "伊丹", "鹿児島", "長崎", "熊本", "宮崎", "小松", "岡山", "広島", "高松", "松山", "高知"]
NORTH_CITIES = ["札幌", "千歳", "青森", "秋田", "山形", "三沢", "旭川", "女満別", "帯広", "釧路", "函館"]

def fetch_and_generate():
    # ... (前段の処理は維持) ...
    
    # ✈️ 便データのループ内でのロジック強化
    for h, m, ampm, carrier, fnum, origin in flights: # origin(出身地)を取得するように正規表現を調整
        # (時刻計算などは維持)
        
        pax, p_type = get_realistic_pax(carrier, fnum, now.hour)
        
        # 🌟 5エリアへの精密な振り分け
        s_key = "P5" # デフォルト国際
        
        if carrier == "JL":
            # 出身地キーワードで1号か2号か判定
            if any(city in origin for city in SOUTH_CITIES):
                s_key = "P1"
            elif any(city in origin for city in NORTH_CITIES):
                s_key = "P2"
            else:
                s_key = "P1" # 判別不能時は暫定1号
                
        elif carrier == "BC": s_key = "P1" # スカイマークは1号
        elif carrier == "NH": s_key = "P3" # ANAは3号(暫定)
        elif carrier in ["ADO", "SNA", "SFJ", "7G"]: s_key = "P4" # LCC/共同運航は4号
        
        stands[s_key] += pax
        # (以降、HTML生成へ)
