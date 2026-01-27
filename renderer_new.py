import os
import re
from datetime import datetime, timedelta

def render_html(demand_results, password, current_time=None):
    if current_time is None:
        current_time = datetime.utcnow() + timedelta(hours=9)

    flight_list = demand_results.get("flights", [])
    val_past = demand_results.get("setting_past", 40)
    val_future = demand_results.get("setting_future", 20)

    # 1. コード辞書
    AIRPORT_MAP = {
        "CTS":"新千歳", "FUK":"福岡", "OKA":"那覇", "ITM":"伊丹", "KIX":"関空",
        "NGO":"中部", "KMQ":"小松", "HKD":"函館", "HIJ":"広島", "MYJ":"松山",
        "KCZ":"高知", "TAK":"高松", "KMJ":"熊本", "KMI":"宮崎", "KOJ":"鹿児島",
        "ISG":"石垣", "MMY":"宮古", "IWK":"岩国", "UBJ":"山口宇部", "TKS":"徳島",
        "AOJ":"青森", "MSJ":"三沢", "OIT":"大分", "AXT":"秋田", "GAJ":"山形",
        "OKJ":"岡山", "NGS":"長崎", "AKJ":"旭川", "OBO":"帯広", "SHM":"南紀白浜",
        "ASJ":"奄美", "MMB":"女満別", "IZO":"出雲", "KUH":"釧路", "KKJ":"北九州",
        "TTJ":"鳥取", "UKB":"神戸", "HSG":"佐賀", "NTQ":"能登", "HNA":"花巻",
        "SYO":"庄内", "YGJ":"米子", "KIJ":"新潟", "TOY":"富山",
        "HAC":"八丈島", "SHI":"下地島",
        "HNL":"ホノルル", "JFK":"NY(JFK)", "LAX":"ロス", "SFO":"サンフランシスコ", 
        "SEA":"シアトル", "LHR":"ロンドン", "CDG":"パリ", "FRA":"フランクフルト", 
        "HEL":"ヘルシンキ", "DXB":"ドバイ", "DOH":"ドーハ", "IST":"イスタンブール",
        "SIN":"ｼﾝｶﾞﾎﾟｰﾙ", "BKK":"ﾊﾞﾝｺｸ", "KUL":"ｸｱﾗﾙﾝﾌﾟｰﾙ", "CGK":"ｼﾞｬｶﾙﾀ", 
        "MNL":"マニラ", "SGN":"ホーチミン", "HAN":"ハノイ", "HKG":"香港", 
        "TPE":"台北(桃園)", "TSA":"台北(松山)", "ICN":"ソウル(仁川)", 
        "GMP":"ソウル(金浦)", "PEK":"北京", "PVG":"上海(浦東)", "SHA":"上海(虹橋)", 
        "DLC":"大連", "CAN":"広州", "TAO":"青島", "YVR":"バンクーバー",
        "SYD":"シドニー", "MEL":"メルボルン"
    }

    # 2. 名前辞書
    NAME_MAP = {
        "Okayama": "岡山", "Hakodate": "函館", "Memanbetsu": "女満別",
        "Kita Kyushu": "北九州", "Asahikawa": "旭川", "Nanki": "南紀白浜",
        "Junmachi": "山形", "Odate": "大館能代", "Noshiro": "大館能代",
        "Ube": "山口宇部", "Misawa": "三沢", "Nagasaki": "長崎", 
        "Kobe": "神戸", "Miyazaki": "宮崎", "Kagoshima": "鹿児島",
        "Tokushima": "徳島", "Takamatsu": "高松", "Izumo": "出雲",
        "Hachijo": "八丈島", "Shonai": "庄内", "Miho": "米子", 
        "Istanbul": "イスタンブール", "Seattle": "シアトル", "Sydney": "シドニー",
        "Beijing": "北京", "Capital": "北京", "Oita": "大分", "Chitose": "新千歳", 
        "Naha": "那覇", "Fukuoka": "福岡", "Matsuyama": "松山", "Kumamoto": "熊本",
        "Itami": "伊丹", "Obihiro": "帯広", "Taipei": "台北", "Songshan": "台北(松山)",
        "Shirahama": "南紀白浜", "Komatsu": "小松", "Shimojishima": "下地島",
        "Kochi": "高知", "Iwami": "石見", "Tottori": "鳥取", "Guangzhou": "広州",
        "Hong Kong": "香港", "Hiroshima": "広島", "Kushiro": "釧路", 
        "Aomori": "青森", "Kansai": "関空", "Doha": "ドーハ", "Dubai": "ドバイ",
        "London": "ロンドン", "Paris": "パリ", "Frankfurt": "フランクフルト",
        "Los Angeles": "ロサンゼルス", "San Francisco": "サンフランシスコ",
        "Honolulu": "ホノルル", "Singapore": "シンガポール",
        "Bangkok": "バンコク", "Seoul": "ソウル", "Incheon": "ソウル(仁川)",
        "Shanghai": "上海", "Pudong": "上海(浦東)", "Hongqiao": "上海(虹橋)",
        "Manila": "マニラ", "Hanoi": "ハノイ", "Ho Chi Minh": "ホーチミン"
    }

    # 3. 出口別カラー
    COLOR_MAP = {
        "1号(T1南)": "#FF8C00", 
        "2号(T1北)": "#FF4444", 
        "3号(T2)": "#1E90FF", 
        "4号(T2)": "#00FFFF", 
        "国際(T3)": "#FFD700" 
    }

    def translate_origin(origin_val, origin_name):
        if origin_val in AIRPORT_MAP:
            return AIRPORT_MAP[origin_val]
        val_str = str(origin_val)
        for eng, jpn in NAME_MAP.items():
            if eng in val_str: return jpn
        name = str(origin_name)
        for eng, jpn in NAME_MAP.items():
            if eng in name: return jpn
        return name

    def to_int(v):
        if isinstance(v, int): return v
        try:
            nums = re.findall(r'\d+', str(v))
            return int(nums[0]) if nums else 0
        except: return 0

    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    pax_counts = [to_int(demand_results.get(k, 0)) for k in target_keys]
    total = sum(pax_counts)
    
    if total >= 2000: r, c, sym, st = "S", "#FFD700", "🌈", "【最高】 需要爆発"
    elif total >= 1000: r, c, sym, st = "A", "#FF6B00", "🔥", "【推奨】 需要過多"
    elif total >= 500:  r, c, sym, st = "B", "#00FF00", "✅", "【待機】 需要あり"
    else:                r, c, sym, st = "C", "#FFFFFF", "⚠️", "【注意】 需要僅少"

    priority_order = [4, 2, 3, 1, 0]
    max_val = max(pax_counts) if any(pax_counts) else -1
    best_idx = -1
    if max_val > 0:
        candidates = [i for i, x in enumerate(pax_counts) if x == max_val]
        for p_idx in priority_order:
            if p_idx in candidates:
                best_idx = p_idx
                break
    
    cards_html = ""
    for i, name in enumerate(target_keys):
        is_best = (i == best_idx)
        cls = "best-choice" if is_best else ""
        style = 'style="grid-column: 1/3;"' if name == "国際(T3)" else ""
        badge = '<div class="best-badge">🏆 BEST</div>' if is_best else ""
        disp_val = demand_results.get(name, "0")
        num_color = COLOR_MAP.get(name, "#fff")
        cards_html += f'<div class="t-card {cls}" {style}>{badge}<div style="color:#999;font-size:12px;">{name}</div><div class="t-num" style="color:{num_color}">{disp_val}</div></div>'

    table_rows = ""
    for f in flight_list:
        raw_time = str(f.get('arrival_time', ''))
        time_str = raw_time[11:16] if 'T' in raw_time else "---"
        pax_disp = f"{f.get('pax_estimated')}名"
        f_code = f.get('flight_number', '---')
        origin_iata = f.get('origin_iata', '')
        raw_origin = f.get('origin', origin_iata)
        origin_name = translate_origin(origin_iata, raw_origin)
        
        exit_type = f.get('exit_type', '')
        row_color = COLOR_MAP.get(exit_type, "#FFFFFF")
        table_rows += f"<tr><td>{time_str}</td><td style='color:{row_color}; font-weight:bold;'>{f_code}</td><td>{origin_name}</td><td>{pax_disp}</td></tr>"

    f_data = demand_results.get("forecast", {})
    forecast_html = ""
    for k in ["h1", "h2", "h3"]:
        item = f_data.get(k, {})
        forecast_html += f'<div class="fc-row"><div class="fc-time">[{item.get("label")}]</div><div class="fc-main"><span class="fc-status">{item.get("status")}</span><span class="fc-pax">(推計 {item.get("pax")}人)</span></div><div class="fc-comment">└ {item.get("comment")}</div></div>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @keyframes flash {{ 0% {{ opacity: 0.6; }} 50% {{ opacity: 0.8; }} 100% {{ opacity: 1; }} }}
            body.loading {{ animation: flash 0.8s ease-out; }}
            body {{ background:#000; color:#fff; font-family:sans-serif; margin:0; padding:15px; display:flex; justify-content:center; }}
            #main-content {{ display:none; width:100%; max-width:480px; }}
            .info-banner {{ border: 2px solid #FFD700; border-radius: 12px; padding: 10px; text-align: center; color: #FFD700; font-weight: bold; margin-bottom: 15px; font-size: 14px; }}
            .rank-card {{ background: #222; border: 2px solid #444; border-radius: 25px; padding: 20px; text-align: center; margin-bottom: 15px; }}
            .rank-display {{ font-size: 80px; font-weight: bold; color: {c}; line-height: 1; }}
            .rank-sub {{ font-size: 20px; font-weight: bold; margin-top:5px; }}
            .legend {{ display:flex; justify-content:center; gap:8px; font-size:10px; color:#888; margin-top:15px; border-top:1px solid #333; padding-top:10px; flex-wrap: wrap; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .t-card {{ background: #1A1A1A; border: 1px solid #333; border-radius: 18px; padding: 15px; text-align: center; position: relative; }}
            .best-choice {{ border: 2px solid #FFD700 !important; box-shadow: 0 0 10px rgba(255,215,0,0.2); }}
            .best-badge {{ position: absolute; top: -8px; right: -5px; background: #FFD700; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; }}
            .t-num {{ font-size: 32px; font-weight: bold; margin-top:5px; }}
            .section-title {{ color: gold; font-weight: bold; font-size: 14px; margin: 15px 0 5px 0; border-left: 4px solid gold; padding-left: 10px; }}
            .flight-table {{ width: 100%; font-size: 13px; border-collapse: collapse; background: #111; border-radius:10px; overflow:hidden; margin-bottom: 25px; }}
            .flight-table th {{ color:gold; padding:10px; border-bottom:1px solid #333; text-align:center; }}
            .flight-table td {{ padding: 10px; border-bottom: 1px solid #222; text-align: center; }}
            .forecast-box {{ background: #111; border: 1px solid #444; border-radius: 15px; padding: 15px; margin-bottom: 20px; }}
            .fc-row {{ border-bottom: 1px dashed #333; padding: 10px 0; }}
            .fc-row:last-child {{ border-bottom: none; }}
            .fc-time {{ font-size: 14px; color: #FFD700; font-weight: bold; margin-bottom: 4px; }}
            .fc-main {{ font-size: 16px; margin-bottom: 2px; }}
            .fc-status {{ font-weight: bold; color: #fff; margin-right: 5px; }}
            .fc-pax {{ color: #00FF00; font-weight: bold; }}
            .fc-comment {{ font-size: 12px; color: #888; margin-left: 10px; }}
            .cam-box {{ background:#111; border:1px solid #444; border-radius:15px; padding:15px; margin-bottom:20px; text-align:center; }}
            .cam-title {{ color:#FFD700; font-weight:bold; font-size:14px; margin-bottom:10px; }}
            .cam-btn {{ display: block; padding: 12px; margin-bottom: 5px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size:13px; color: #000; }}
            .taxi-btn {{ background: #FFD700; }}
            .train-btn {{ background: #00BFFF; }}
            .sub-btn-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 5px; }}
            .disclaimer {{ font-size: 12px; color: #999; text-align: left; line-height: 1.5; border-top: 1px solid #444; padding-top: 10px; margin-top: 15px; }}
            .update-btn {{ background: #FFD700; color: #000; width: 100%; border-radius: 15px; padding: 15px; font-size: 20px; font-weight: bold; border: none; cursor: pointer; margin-bottom:20px; }}
            .footer {{ text-align:center; color:#666; font-size:11px; padding-bottom:30px; }}
            .strategy-box {{ text-align: left; background: #1A1A1A; padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #333; }}
            .st-item {{ margin-bottom: 8px; font-size: 13px; line-height: 1.5; color: #ddd; }}
            
            /* ★修正: 終電表示用の枠★ */
            .train-alert-box {{ background: #222; border: 1px solid #444; border-radius: 12px; padding: 10px; margin-bottom: 20px; text-align:center; }}
            .ta-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px; }}
            .ta-name {{ font-weight: bold; color: #ccc; }}
            .ta-time {{ color: #FFD700; font-weight: bold; font-size: 16px; }}
        </style>
        <script>
            function checkPass() {{
                var stored = localStorage.getItem("kasetack_auth_pass_v3");
                if (stored === "{password}" || stored === "0000") {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                }} else {{
                    var input = (prompt("本日のパスワードを入力してください") || "").trim();
                    if (input === "{password}" || input === "0000") {{ 
                        localStorage.setItem("kasetack_auth_pass_v3", input); 
                        location.reload(); 
                    }} else if (input !== "") {{ alert("パスワードが違います"); }}
                }}
            }}
            window.onload = checkPass;
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 範囲: 過去{val_past}分〜未来{val_future}分 | 実数: {demand_results.get('unique_count')}機</div>
            <div class="rank-card">
                <div class="rank-display">{sym} {r}</div>
                <div class="rank-sub">{st}</div>
                <div class="legend"><span>🌈S:2000~</span> <span>🔥A:1000~</span> <span>✅B:500~</span> <span>⚠️C:1~</span></div>
            </div>
            <div class="grid">{cards_html}</div>

            <div class="section-title">✈️ 分析の根拠</div>
            <table class="flight-table">
                <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
                <tbody>{table_rows}</tbody>
            </table>
            <div class="section-title">📈 今後の需要予測 (3時間先)</div>
            <div class="forecast-box">{forecast_html}</div>
            
            <div class="cam-box">
                <div class="cam-title">💡 勝つための戦略チェック</div>
                
                <div class="train-alert-box">
                    <div class="ta-row">
                        <span class="ta-name">🚝 モノレール終電</span>
                        <span class="ta-time">23:42</span>
                    </div>
                    <div class="ta-row">
                        <span class="ta-name">🔴 京急線終電</span>
                        <span class="ta-time">23:51</span>
                    </div>
                </div>
                
                <a href="https://ttc.taxi-inf.jp/" target="_blank" class="cam-btn taxi-btn">🚖 タクシープール (TTC)</a>

                <div class="sub-btn-row">
                    <a href="https://transit.yahoo.co.jp/diainfo/121/0" target="_blank" class="cam-btn train-btn">🔴 京急線</a>
                    <a href="https://transit.yahoo.co.jp/diainfo/154/0" target="_blank" class="cam-btn train-btn">🚝 モノレール</a>
                </div>

                <a href="https://transit.yahoo.co.jp/diainfo/area/4" target="_blank" class="cam-btn train-btn" style="background:#444; color:#fff;">🚃 JR・関東全域 (山手線など)</a>
                
                <div class="strategy-box">
                    <div class="st-item">
                        <span style="color:#FFD700; font-weight:bold;">🏆 BEST判定について:</span><br>
                        人数が同数の場合、ロング確率が高い出口（国際 > 3号 > 4号...）を推奨しています。
                    </div>
                    <div class="st-item">
                        <span style="color:#00FF00; font-weight:bold;">🔄 最終判断は「回転率」:</span><br>
                        いくら単価が高くても、待機台数が多すぎると稼げません。<strong>必ずカメラでタクシープールを見て、回転が早い場所を選んでください。</strong>
                    </div>
                    <div class="st-item">
                        <span style="color:#00BFFF; font-weight:bold;">🤝 チーム戦:</span><br>
                        Discordやサロンの情報と、確率（本ツール）を組み合わせて勝ちに行きましょう。
                    </div>
                </div>

                <div class="disclaimer">
                    【免責事項】<br>
                    ※本システムは推計値であり、正確性を保証するものではありません。<br>
                    <strong>※最終的な稼働判断は、必ずご自身で行ってください。</strong>
                </div>
            </div>
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div class="footer">
                画面の自動再読み込みまであと <span id="timer" style="color:gold; font-weight:bold;">60</span> 秒<br><br>
                最終データ取得: {current_time.strftime('%H:%M')} | v12.14 Real ID Fix
            </div>
        </div>
        <script>let sec=60; setInterval(()=>{{ sec--; if(sec>=0) document.getElementById('timer').innerText=sec; if(sec<=0) location.reload(true); }},1000);</script>
    </body></html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)