import os
from datetime import datetime

def render_html(data, password):
    """
    分析済みのデータ(絞り込み済み)だけを見やすく表示する
    パスワードロック付き(日付)
    """
    update_time = data.get("update_time", datetime.now().strftime('%H:%M'))
    forecast = data.get("forecast", {})
    
    # Analyzerですでに「条件に合う便」だけに絞られたリストを受け取る
    flights = data.get("flights", [])
    
    # カード表示用
    cards_html = ""
    total_pax = 0
    target_keys = ["1号(T1南)", "2号(T1北)", "3号(T2)", "4号(T2)", "国際(T3)"]
    
    for key in target_keys:
        val = data.get(key, 0)
        total_pax += val
        status_color = "text-gray-500"
        if val >= 300: status_color = "text-red-600 font-bold"
        elif val >= 100: status_color = "text-green-600 font-bold"
            
        cards_html += f"""
        <div class="bg-white p-4 rounded-lg shadow text-center">
            <div class="text-sm text-gray-500">{key}</div>
            <div class="text-2xl {status_color}">{val}<span class="text-xs text-gray-400">人</span></div>
        </div>
        """

    # 全体ステータス
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

    # フライトリスト（条件に合致したものだけを表示）
    flight_rows = ""
    # 万が一大量にあっても画面が壊れないよう、上位50件に制限して表示する安全策
    display_flights = flights[:50] 
    
    for f in display_flights:
        t_str = f.get('arrival_time', '')
        time_display = t_str[11:16] if len(t_str) >= 16 else t_str
        
        flight_rows += f"""
        <tr class="border-b">
            <td class="py-2 px-2">{time_display}</td>
            <td class="py-2 px-2 font-bold">{f.get('flight_number')}</td>
            <td class="py-2 px-2 text-xs text-gray-600">{f.get('origin')}</td>
            <td class="py-2 px-2 text-right">{f.get('terminal')}</td>
        </tr>
        """

    # 3時間予測
    forecast_html = ""
    for k in ["h1", "h2", "h3"]:
        item = forecast.get(k, {})
        forecast_html += f"""
        <div class="mb-3 border-l-4 border-blue-500 pl-3">
            <div class="text-sm font-bold text-gray-600">[{item.get('label', '--:--')}]</div>
            <div class="text-lg">{item.get('status', '---')} <span class="text-sm text-gray-500">(推計 {item.get('pax', 0)}人)</span></div>
        </div>
        """

    # HTML生成（パスワードロック付き）
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>羽田タクシー需要予測</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            // パスワードロック (0122などの日付)
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
                <div class="text-xs text-gray-500 mb-1">⚠️ 範囲: 直近75分 | 対象: {len(flights)}機</div>
                <div class="text-3xl font-black text-gray-800 mb-1">{main_status}</div>
                <div class="text-xs text-gray-400">Updates Automatically</div>
            </div>

            <div class="grid grid-cols-2 gap-3 mb-6">
                {cards_html}
            </div>

            <div class="bg-white p-4 rounded-xl shadow-md mb-6">
                <h3 class="font-bold text-gray-700 mb-2 border-b pb-2">✈️ 直近の到着便 (条件合致のみ)</h3>
                <div class="overflow-y-auto max-h-96">
                    <table class="w-full text-sm text-left">
                        <thead class="text-xs text-gray-500 bg-gray-50 sticky top-0">
                            <tr>
                                <th class="px-2 py-1">時刻</th>
                                <th class="px-2 py-1">便名</th>
                                <th class="px-2 py-1">発地</th>
                                <th class="px-2 py-1 text-right">T</th>
                            </tr>
                        </thead>
                        <tbody>
                            {flight_rows}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="bg-white p-4 rounded-xl shadow-md mb-6">
                <h3 class="font-bold text-gray-700 mb-2">📈 今後の需要予測</h3>
                {forecast_html}
            </div>

            <div class="text-center text-xs text-gray-400 mt-8 mb-10">
                <div>最終データ取得: {update_time}</div>
                <div>v9.3 Stable</div>
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML生成完了")