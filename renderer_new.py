# renderer_new.py
import os
from datetime import datetime

def render_html(data, password):
    """
    分析結果(data)とパスワードを受け取り、
    スマホで見やすいHTML(index.html)を生成する
    """
    
    # 1. データの整理
    # Analyzerから渡された "update_time" を取得（なければ現在時刻）
    update_time = data.get("update_time", datetime.now().strftime('%H:%M'))
    
    # 予測データ
    forecast = data.get("forecast", {})
    flights = data.get("flights", [])
    
    # カード表示用HTML（T1, T2, T3の数字）
    cards_html = ""
    total_pax = 0
    
    # 辞書から数字データだけを取り出してカードを作る
    # (forecastやflightsなどのメタデータは除外する)
    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    
    for key in target_keys:
        val = data.get(key, 0) # キーがなければ0
        total_pax += val
        
        # 混雑度判定
        status_color = "text-gray-500"
        if val >= 300: status_color = "text-red-600 font-bold"
        elif val >= 100: status_color = "text-green-600 font-bold"
            
        cards_html += f"""
        <div class="bg-white p-4 rounded-lg shadow text-center">
            <div class="text-sm text-gray-500">{key}</div>
            <div class="text-2xl {status_color}">{val}<span class="text-xs text-gray-400">人</span></div>
        </div>
        """

    # 全体ステータス判定
    main_status = "🟢 閑散"
    main_bg = "bg-blue-50"
    if total_pax >= 1000:
        main_status = "🌈 S (超混雑)"
        main_bg = "bg-purple-100"
    elif total_pax >= 600:
        main_status = "🔥 A (混雑)"
        main_bg = "bg-red-100"
    elif total_pax >= 200:
        main_status = "✅ B (通常)"
        main_bg = "bg-green-100"

    # フライトリストのHTML生成
    flight_rows = ""
    for f in flights:
        # 時間の整形 (2025-01-22T19:45:00 -> 19:45)
        t_str = f.get('arrival_time', '')
        time_display = t_str[11:16] if len(t_str) >= 16 else t_str
        
        flight_rows += f"""
        <tr class="border-b">
            <td class="py-2 px-2">{time_display}</td>
            <td class="py-2 px-2 font-bold">{f.get('flight_number')}</td>
            <td class="py-2 px-2 text-xs text-gray-600">{f.get('origin')}</td>
            <td class="py-2 px-2 text-right">{f.get('pax_estimated')}名</td>
        </tr>
        """

    # 3時間予測のHTML生成
    forecast_html = ""
    for k in ["h1", "h2", "h3"]:
        item = forecast.get(k, {})
        forecast_html += f"""
        <div class="mb-3 border-l-4 border-blue-500 pl-3">
            <div class="text-sm font-bold text-gray-600">[{item.get('label', '--:--')}]</div>
            <div class="text-lg">{item.get('status', '---')} <span class="text-sm text-gray-500">(推計 {item.get('pax', 0)}人)</span></div>
            <div class="text-xs text-gray-400">└ {item.get('comment', '---')}</div>
        </div>
        """

    # HTMLテンプレート
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>羽田タクシー需要予測</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            // 簡易パスワードロック
            window.onload = function() {{
                const input = prompt("本日のパスワードを入力してください");
                if (input !== "{password}") {{
                    document.body.innerHTML = "<div class='p-10 text-center'>🔒 アクセス拒否<br>パスワードが違います</div>";
                }} else {{
                    document.getElementById("main-content").style.display = "block";
                }}
            }}
        </script>
    </head>
    <body class="bg-gray-100 text-gray-800">
        <div id="main-content" style="display:none;" class="max-w-md mx-auto p-4">
            
            <div class="{main_bg} p-4 rounded-xl shadow-md mb-4 text-center border border-gray-200">
                <div class="text-xs text-gray-500 mb-1">⚠️ 範囲: 直近75分 | 実数: {len(flights)}機</div>
                <div class="text-3xl font-black text-gray-800 mb-1">{main_status}</div>
                <div class="text-xs text-gray-400">🌈S:1000~ 🔥A:600~ ✅B:200~</div>
            </div>

            <div class="grid grid-cols-2 gap-3 mb-6">
                {cards_html}
            </div>

            <div class="bg-white p-4 rounded-xl shadow-md mb-6">
                <h3 class="font-bold text-gray-700 mb-2 border-b pb-2">✈️ 直近の到着便 (遅延含む)</h3>
                <div class="overflow-y-auto max-h-64">
                    <table class="w-full text-sm text-left">
                        <thead class="text-xs text-gray-500 bg-gray-50">
                            <tr>
                                <th class="px-2 py-1">時刻</th>
                                <th class="px-2 py-1">便名</th>
                                <th class="px-2 py-1">発地</th>
                                <th class="px-2 py-1 text-right">人数</th>
                            </tr>
                        </thead>
                        <tbody>
                            {flight_rows}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="bg-white p-4 rounded-xl shadow-md mb-6">
                <h3 class="font-bold text-gray-700 mb-2">📈 今後の需要予測 (3時間先)</h3>
                {forecast_html}
            </div>

            <div class="text-center text-xs text-gray-400 mt-8 mb-10">
                <div>最新情報に更新</div>
                <div>画面の自動再読み込みまであと <span id="timer">60</span> 秒</div>
                <div class="mt-2">最終データ取得: {update_time} | v8.5 Fixed</div>
            </div>
        </div>

        <script>
            // 60秒カウントダウンタイマー
            let timeLeft = 60;
            const timerElement = document.getElementById('timer');
            setInterval(() => {{
                if (timeLeft <= 0) {{
                    location.reload(); 
                }} else {{
                    timerElement.textContent = timeLeft;
                    timeLeft--;
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    """

    # ファイル書き出し
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML生成完了")