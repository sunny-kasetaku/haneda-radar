import os
import re
import json
from datetime import datetime, timedelta

def render_html(demand_results, password, current_time=None):
    if current_time is None:
        current_time = datetime.utcnow() + timedelta(hours=9)

    flight_list = demand_results.get("flights", [])
    val_past = demand_results.get("setting_past", 40)
    val_future = demand_results.get("setting_future", 20)

    # 1. 空港コード辞書 (完全一致)
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
    
    # 2. 都市名辞書 (部分一致)
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
        "Manila": "マニラ", "Hanoi": "ハノイ", "Ho Chi Minh": "ホーチミン",
        "Chicago": "シカゴ", "Dallas": "ダラス", "Atlanta": "アトランタ",
        "Detroit": "デトロイト", "Shenzhen": "深セン", "Dalian": "大連",
        "Qingdao": "青島", "Gimpo": "ソウル(金浦)", "Helsinki": "ヘルシンキ",
        "Minneapolis": "ミネアポリス", "George Bush": "ヒューストン", 
        "Washington": "ワシントン", "Pearson": "トロント", "Toronto": "トロント",
        "Leonardo": "ローマ", "Fiumicino": "ローマ", "Indira": "デリー"
    }

    def translate_origin(origin_val, origin_name):
        if origin_val in AIRPORT_MAP: return AIRPORT_MAP[origin_val]
        val_str = str(origin_val)
        for eng, jpn in NAME_MAP.items():
            if eng in val_str: return jpn
        name = str(origin_name)
        for eng, jpn in NAME_MAP.items():
            if eng in name: return jpn
        return name

    # JSに渡すためのデータ整形
    final_flights_for_js = []
    
    for f in flight_list:
        origin_iata = f.get('origin_iata', '')
        raw_origin = f.get('origin', origin_iata)
        jpn_origin = translate_origin(origin_iata, raw_origin)
        
        term = str(f.get('terminal', ''))
        exit_type = f.get('exit_type', '')

        if not exit_type:
            if term == "3" or term == "I": exit_type = "国際(T3)"
            elif term == "2": exit_type = "3号(T2)"
            elif term == "1": exit_type = "1号(T1南)"
            else: exit_type = "国際(T3)"

        final_flights_for_js.append({
            'arrival_time': str(f.get('arrival_time', '')),
            'flight_number': f.get('flight_number', '---'),
            'origin': jpn_origin,
            'pax': int(f.get('pax_estimated', 200)),
            'exit_type': exit_type,
            'terminal': term
        })
    
    json_data = json.dumps(final_flights_for_js, ensure_ascii=False)

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
            .rank-display {{ font-size: 80px; font-weight: bold; color: #FFD700; line-height: 1; }}
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
            .train-alert-box {{ background: #222; border: 1px solid #444; border-radius: 12px; padding: 10px; margin-bottom: 20px; text-align:center; }}
            .ta-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px; }}
            .ta-name {{ font-weight: bold; color: #ccc; }}
            .ta-time {{ color: #FFD700; font-weight: bold; font-size: 16px; }}
        </style>
        
        <script>
            const FLIGHT_DATA = {json_data};
            const SETTING_PAST = {val_past};
            const SETTING_FUTURE = {val_future};
            
            function checkPass() {{
                var stored = localStorage.getItem("kasetack_auth_pass_v3");
                if (stored === "{password}" || stored === "0000") {{
                    document.getElementById('main-content').style.display = 'block';
                    document.body.classList.add('loading');
                    initApp();
                }} else {{
                    var input = (prompt("本日のパスワードを入力してください") || "").trim();
                    if (input === "{password}" || input === "0000") {{ 
                        localStorage.setItem("kasetack_auth_pass_v3", input); 
                        location.reload(); 
                    }} else if (input !== "") {{ alert("パスワードが違います"); }}
                }}
            }}
            window.onload = checkPass;

            function initApp() {{
                updateDisplay();
                setInterval(updateDisplay, 60000); 
            }}

            function updateDisplay() {{
                const now = new Date();
                const startTime = new Date(now.getTime() - SETTING_PAST * 60000);
                const endTime = new Date(now.getTime() + SETTING_FUTURE * 60000);

                let counts = {{ "1号(T1南)":0, "2号(T1北)":0, "3号(T2)":0, "4号(T2)":0, "国際(T3)":0 }};
                let tableHtml = "";
                let fcCounts = [0, 0, 0];

                FLIGHT_DATA.forEach(f => {{
                    let fDate = new Date(f.arrival_time);
                    let eType = f.exit_type;
                    if (!counts.hasOwnProperty(eType)) eType = "国際(T3)";

                    if (fDate >= startTime && fDate <= endTime) {{
                        counts[eType] += f.pax;
                        let h = fDate.getHours().toString().padStart(2, '0');
                        let m = fDate.getMinutes().toString().padStart(2, '0');
                        let timeStr = h + ":" + m;
                        
                        let color = "#FFFFFF";
                        if (eType === "1号(T1南)") color = "#FF8C00";
                        if (eType === "2号(T1北)") color = "#FF4444";
                        if (eType === "3号(T2)") color = "#1E90FF";
                        if (eType === "4号(T2)") color = "#00FFFF";
                        if (eType === "国際(T3)") color = "#FFD700";
                        
                        tableHtml += `<tr><td>${{timeStr}}</td><td style='color:${{color}}; font-weight:bold;'>${{f.flight_number}}</td><td>${{f.origin}}</td><td>${{f.pax}}名</td></tr>`;
                    }}
                    
                    let diffMs = fDate - now;
                    let diffMins = diffMs / 60000;
                    if (diffMins >= 0 && diffMins < 60) fcCounts[0] += f.pax;
                    if (diffMins >= 60 && diffMins < 120) fcCounts[1] += f.pax;
                    if (diffMins >= 120 && diffMins < 180) fcCounts[2] += f.pax;
                }});

                document.getElementById('flight-table-body').innerHTML = tableHtml;
                document.getElementById('count-t1s').innerText = counts["1号(T1南)"];
                document.getElementById('count-t1n').innerText = counts["2号(T1北)"];
                document.getElementById('count-t2-3').innerText = counts["3号(T2)"];
                document.getElementById('count-t2-4').innerText = counts["4号(T2)"];
                document.getElementById('count-t3').innerText = counts["国際(T3)"];
                
                document.querySelectorAll('.t-card').forEach(el => el.classList.remove('best-choice'));
                document.querySelectorAll('.best-badge').forEach(el => el.remove());
                
                let maxVal = -1;
                let bestKey = "";
                let priorityKeys = ["国際(T3)", "4号(T2)", "3号(T2)", "2号(T1北)", "1号(T1南)"];
                let allMax = Math.max(...Object.values(counts));
                
                if (allMax > 0) {{
                    for (let k of priorityKeys) {{
                        if (counts[k] === allMax) {{
                            bestKey = k;
                            break;
                        }}
                    }}
                }}
                
                let targetId = "";
                if(bestKey === "1号(T1南)") targetId = "card-t1s";
                if(bestKey === "2号(T1北)") targetId = "card-t1n";
                if(bestKey === "3号(T2)") targetId = "card-t2-3";
                if(bestKey === "4号(T2)") targetId = "card-t2-4";
                if(bestKey === "国際(T3)") targetId = "card-t3";
                
                if(targetId) {{
                    let bestEl = document.getElementById(targetId);
                    bestEl.classList.add('best-choice');
                    bestEl.insertAdjacentHTML('afterbegin', '<div class="best-badge">🏆 BEST</div>');
                }}
                
                let total = Object.values(counts).reduce((a,b)=>a+b, 0);
                let r="C", c="#FFFFFF", sym="⚠️", st="【注意】 需要僅少";
                if(total >= 2000) {{ r="S"; c="#FFD700"; sym="🌈"; st="【最高】 需要爆発"; }}
                else if(total >= 1000) {{ r="A"; c="#FF6B00"; sym="🔥"; st="【推奨】 需要過多"; }}
                else if(total >= 500) {{ r="B"; c="#00FF00"; sym="✅"; st="【待機】 需要あり"; }}
                
                document.getElementById('rank-disp').innerText = sym + " " + r;
                document.getElementById('rank-disp').style.color = c;
                document.getElementById('rank-sub').innerText = st;
                document.getElementById('total-count').innerText = total;

                updateForecast('fc-0', fcCounts[0]);
                updateForecast('fc-1', fcCounts[1]);
                updateForecast('fc-2', fcCounts[2]);
            }}
            
            function updateForecast(id, pax) {{
                let status = "👀 通常";
                if(pax >= 1000) status = "🔥 高";
                else if(pax >= 500) status = "✅ 中";
                
                document.getElementById(id + '-pax').innerText = "(推計 " + pax + "人)";
                document.getElementById(id + '-status').innerText = status;
            }}
        </script>
    </head>
    <body>
        <div id="main-content">
            <div class="info-banner">⚠️ 範囲: 過去{val_past}分〜未来{val_future}分 | 実数: <span id="total-count">---</span>機</div>
            
            <div class="rank-card">
                <div id="rank-disp" class="rank-display">---</div>
                <div id="rank-sub" class="rank-sub">集計中...</div>
                <div class="legend"><span>🌈S:2000~</span> <span>🔥A:1000~</span> <span>✅B:500~</span> <span>⚠️C:1~</span></div>
            </div>
            
            <div class="grid">
                <div id="card-t1s" class="t-card"><div style="color:#999;font-size:12px;">1号(T1南)</div><div id="count-t1s" class="t-num" style="color:#FF8C00">0</div></div>
                <div id="card-t1n" class="t-card"><div style="color:#999;font-size:12px;">2号(T1北)</div><div id="count-t1n" class="t-num" style="color:#FF4444">0</div></div>
                <div id="card-t2-3" class="t-card"><div style="color:#999;font-size:12px;">3号(T2)</div><div id="count-t2-3" class="t-num" style="color:#1E90FF">0</div></div>
                <div id="card-t2-4" class="t-card"><div style="color:#999;font-size:12px;">4号(T2)</div><div id="count-t2-4" class="t-num" style="color:#00FFFF">0</div></div>
                <div id="card-t3" class="t-card" style="grid-column: 1/3;"><div style="color:#999;font-size:12px;">国際(T3)</div><div id="count-t3" class="t-num" style="color:#FFD700">0</div></div>
            </div>

            <div class="section-title">✈️ 分析の根拠</div>
            <table class="flight-table">
                <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
                <tbody id="flight-table-body"></tbody>
            </table>
            
            <div class="section-title">📈 今後の需要予測 (3時間先)</div>
            <div class="forecast-box">
                <div class="fc-row"><div class="fc-time">[現在〜]</div><div class="fc-main"><span id="fc-0-status" class="fc-status">---</span><span id="fc-0-pax" class="fc-pax">---</span></div></div>
                <div class="fc-row"><div class="fc-time">[+1時間]</div><div class="fc-main"><span id="fc-1-status" class="fc-status">---</span><span id="fc-1-pax" class="fc-pax">---</span></div></div>
                <div class="fc-row"><div class="fc-time">[+2時間]</div><div class="fc-main"><span id="fc-2-status" class="fc-status">---</span><span id="fc-2-pax" class="fc-pax">---</span></div></div>
            </div>
            
            <div class="cam-box">
                <div class="cam-title">💡 勝つための戦略チェック</div>
                <div class="train-alert-box">
                    <div class="ta-row"><span class="ta-name">🚝 モノレール終電</span><span class="ta-time">23:42</span></div>
                    <div class="ta-row"><span class="ta-name">🔴 京急線終電</span><span class="ta-time">23:51</span></div>
                </div>
                <a href="https://ttc.taxi-inf.jp/" target="_blank" class="cam-btn taxi-btn">🚖 タクシープール (TTC)</a>
                
                <div class="cam-title" style="margin-top:15px;">👑 最終確認 (公式情報)</div>
                <div style="font-size:11px; color:#999; margin-bottom:5px;">※表示されない便がある時や、正確な遅延情報を知りたい時に。</div>
                <div class="sub-btn-row">
                    <a href="https://tokyo-haneda.com/flight/flightInfo_int.html" target="_blank" class="cam-btn" style="background:#fff; color:#000;">✈️ 国際線 (T3)</a>
                    <a href="https://tokyo-haneda.com/flight/flightInfo_dms.html" target="_blank" class="cam-btn" style="background:#ddd; color:#000;">✈️ 国内線 (T1/T2)</a>
                </div>

                <div class="sub-btn-row" style="margin-top:5px;">
                    <a href="https://transit.yahoo.co.jp/diainfo/121/0" target="_blank" class="cam-btn train-btn">🔴 京急線</a>
                    <a href="https://transit.yahoo.co.jp/diainfo/154/0" target="_blank" class="cam-btn train-btn">🚝 モノレール</a>
                </div>
                <a href="https://transit.yahoo.co.jp/diainfo/area/4" target="_blank" class="cam-btn train-btn" style="background:#444; color:#fff;">🚃 JR・関東全域 (山手線など)</a>
                
                <div class="strategy-box">
                    <div class="st-item"><span style="color:#FFD700; font-weight:bold;">📊 本ツールの強み:</span><br>公式サイトにはない「合計人数」と「未来予測」で、瞬時に稼働判断ができます。基本はツールでOKです。</div>
                    <div class="st-item"><span style="color:#00FF00; font-weight:bold;">🔄 最終判断は「回転率」:</span><br>いくら単価が高くても、待機台数が多すぎると稼げません。<strong>必ずカメラでタクシープールを見て、回転が早い場所を選んでください。</strong></div>
                    <div class="st-item"><span style="color:#00BFFF; font-weight:bold;">🤝 チーム戦:</span><br>Discordやサロンの情報と、確率（本ツール）を組み合わせて勝ちに行きましょう。</div>
                </div>
                <div class="disclaimer">
                    【免責事項】<br>
                    ※通信のタイムラグにより、一部の便（特に大幅遅延時など）が表示されない場合があります。<br>
                    ※最終的な正解は、上記の「羽田公式サイト」で必ず確認してください。<br>
                    <strong>※最終的な稼働判断は、必ずご自身で行ってください。</strong>
                </div>
            </div>
            
            <button class="update-btn" onclick="location.reload(true)">最新情報に更新</button>
            <div class="footer">
                データ取得: {current_time.strftime('%H:%M')} (API) | 表示更新: <span id="last-update">Now</span><br>
                <span style="font-size:10px; color:#666;">次のリロードまであと <span id="timer" style="color:gold; font-weight:bold;">60</span> 秒</span>
            </div>
        </div>
        <script>
            // 画面タイマー & 自動リロード
            let sec=60; 
            setInterval(()=>{{ 
                sec--; 
                if(document.getElementById('timer')) document.getElementById('timer').innerText = sec;
                if(sec <= 0) location.reload(true);
            }}, 1000);
            
            // 表示更新時刻
            setInterval(()=>{{
                let d=new Date();
                let m = d.getMinutes().toString().padStart(2,'0');
                if(document.getElementById('last-update')) document.getElementById('last-update').innerText = d.getHours()+":"+m;
            }}, 60000);
        </script>
    </body></html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)