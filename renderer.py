import json
from config import CONFIG

# HTMLテンプレート（v4.1 精度向上・鮮度可視化版）
HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK 羽田レーダー v4.1</title>
<style>
    body { background: #0a0a0a; color: #eee; font-family: sans-serif; padding: 10px; margin: 0; }
    .container { max-width: 600px; margin: 0 auto; }
    
    /* 更新時刻バッジ（一等地位） */
    .freshness-badge { text-align: center; margin-bottom: 8px; }
    .time-chip { background: #333; color: #FFD700; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; border: 1px solid #444; }
    
    .rank-box { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 3px solid [[RANK_COLOR]]; text-align: center; margin-bottom: 10px; }
    .rank-main { font-size: 3.5rem; font-weight: 900; color: [[RANK_COLOR]]; margin: 0; }
    .legend { background: #111; padding: 10px; border-radius: 8px; font-size: 0.7rem; color: #888; display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; margin-bottom: 15px; border: 1px solid #333; }
    .legend-item { text-align: center; }
    .stand-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px; }
    .stand-card { background: #222; padding: 12px; border-radius: 10px; border: 1px solid #444; text-align: center; }
    .stand-card.intl { grid-column: span 2; border-color: #FFD700; }
    .val { font-size: 1.6rem; font-weight: bold; color: #fff; display: block; }
    .pool-val { font-size: 0.9rem; color: #FFD700; font-weight: bold; margin-top: 4px; display: block; } 
    .label { font-size: 0.75rem; color: #aaa; }
    .advice-box { background: #222; border-left: 6px solid #FFD700; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 0.9rem; }
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #111; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 2px solid #333; padding: 10px; }
    .flight-list td { padding: 10px; border-bottom: 1px solid #222; }
    .update-btn { background: #FFD700; color: #000; border: none; padding: 20px; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 15px; cursor: pointer; margin-top: 15px; }
    .timer-info { text-align: center; margin-top: 10px; color: #888; font-size: 0.8rem; }
    #timer { color: #FFD700; font-weight: bold; }
    .notice { color: #FFD700; background: rgba(255, 215, 0, 0.1); padding: 10px; border-radius: 5px; font-size: 0.8rem; text-align: center; margin-bottom: 15px; border: 1px solid #FFD700; }
</style></head>
<body onload="startTimer()"><div class="container">
    <div class="freshness-badge">
        <span class="time-chip">最新データ：[[TIME]] 取得</span>
    </div>

    <div class="notice">
        <b>⚠️ 案内</b>：本データは <b>15分ごと</b> に自動更新されます。<br>
        解析範囲：入庫タイムラグ考慮 (現物 -30分 〜 未来 +45分)
    </div>

    <div class="rank-box">
        <p class="rank-main">[[RANK]]</p>
        <p style="color:#fff; font-weight:bold; margin:5px 0;">[[RANK_MSG]]</p>
    </div>

    <div class="legend">
        <div class="legend-item"><b style="color:#FFD700">S</b>:800~</div>
        <div class="legend-item"><b style="color:#FF4500">A</b>:400~</div>
        <div class="legend-item"><b style="color:#00ff7f">B</b>:100~</div>
        <div class="legend-item"><b style="color:#ccc">C</b>:1~</div>
        <div class="legend-item"><b>D</b>:0</div>
    </div>

    <div class="stand-grid">[[CARDS]]</div>

    <div class="advice-box"><strong>⚡ 参謀アドバイス：</strong><br>[[REASON]]</div>

    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
        <tbody>[[ROWS]]</tbody>
    </table>

    <button class="update-btn" onclick="location.reload()">最新情報に更新</button>
    <div class="timer-info">画面の自動更新まであと <span id="timer">60</span> 秒</div>
    
    <div style="text-align:center; font-size:0.7rem; color:#444; margin-top:20px;">
        KASETACK v4.1 | 現場主義・時給最大化モデル
    </div>
</div>
<script>
    function startTimer() {
        let timeLeft = 60; 
        const timerDisplay = document.getElementById('timer');
        setInterval(() => {
            timeLeft--;
            if (timerDisplay) timerDisplay.innerText = timeLeft;
            if (timeLeft <= 0) location.reload();
        }, 1000);
    }
</script>
</body></html>
"""

def run_render():
    with open(CONFIG["RESULT_JSON"], "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tp = data["total_pax"]
    # ランク判定
    if tp > 800: rk, col, msg = ("🌈 S", "#FFD700", "【激熱】即出撃！")
    elif tp > 400: rk, col, msg = ("🔥 A", "#FF4500", "【推奨】安定需要")
    elif tp > 100: rk, col, msg = ("✨ B", "#00ff7f", "【注意】小規模")
    elif tp > 0:   rk, col, msg = ("☁️ C", "#ccc", "【待機】微かな需要")
    else:          rk, col, msg = ("🌑 D", "#888", "【撤退】需要なし")
    
    # 最も需要が高い乗り場を特定
    best_key = max(data["stands"], key=data["stands"].get) if tp > 0 else "P1"
    
    cards = ""
    labels = ["1号 (T1南)", "2号 (T1北)", "3号 (T2)", "4号 (T2)", "国際 (T3)"]
    for i, label in enumerate(labels, 1):
        key = f"P{i}"
        is_best = "border: 2px solid #FFD700;" if key == best_key and tp > 0 else ""
        is_intl = "intl" if key == "P5" else ""
        
        # プール予測値を取得（ない場合は --- 表示）
        pool_est = data.get("pool_preds", {}).get(key, "---") 
        
        cards += (
            f'<div class="stand-card {is_intl}" style="{is_best}">'
            f'<span class="label">{label}</span>'
            f'<span class="val">{data["stands"].get(key, 0)}人</span>'
            f'<span class="pool-val">プール予測: {pool_est}台</span>'
            f'</div>'
        )

    # 1時間回転を意識したアドバイス生成
    best_num = best_key.replace('P', '')
    if tp > 0:
        advice = f"現在から75分後までの実需を捕捉。{best_num}番乗り場方面に強い需要。1時間以内の回転が期待できます。"
    else:
        advice = "対象期間内に大きな到着便がありません。無理な入庫は避け、時給維持を優先してください。"

    rows = ""
    for r in data["rows"]:
        rows += f"<tr><td>{r['time']}</td><td>{r['flight']}</td><td>{r['origin']}</td><td>{r['pax']}名</td></tr>"

    # プレースホルダ置換
    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[RANK_COLOR]]", col).replace("[[RANK_MSG]]", msg) \
        .replace("[[CARDS]]", cards) \
        .replace("[[REASON]]", advice) \
        .replace("[[ROWS]]", rows if rows else "<tr><td colspan='4'>対象なし</td></tr>") \
        .replace("[[TIME]]", data["update_time"])

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML Rendered: {data['update_time']} version (v4.1)")

if __name__ == "__main__":
    run_render()
