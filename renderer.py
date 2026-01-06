import json
from config import CONFIG

HTML_TEMPLATE = """
<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KASETACK 羽田リアルタイム解析</title>
<style>
    body { background: #0a0a0a; color: #eee; font-family: sans-serif; padding: 10px; margin: 0; }
    .container { max-width: 600px; margin: 0 auto; }
    .rank-box { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 3px solid [[RANK_COLOR]]; text-align: center; margin-bottom: 10px; }
    .rank-main { font-size: 3.5rem; font-weight: 900; color: [[RANK_COLOR]]; margin: 0; }
    .stand-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px; }
    .stand-card { background: #222; padding: 15px; border-radius: 10px; border: 1px solid #444; text-align: center; }
    .stand-card.intl { grid-column: span 2; border-color: #FFD700; }
    .val { font-size: 1.8rem; font-weight: bold; color: #fff; display: block; }
    .label { font-size: 0.8rem; color: #aaa; }
    .best-stand { border-color: #00ff7f; background: rgba(0,255,127,0.1); }
    .criteria-badge { background: #333; color: #FFD700; padding: 5px 10px; border-radius: 5px; font-size: 0.75rem; display: inline-block; margin-bottom: 10px; }
    .advice-box { background: #222; border-left: 6px solid #FFD700; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    .flight-list { width: 100%; border-collapse: collapse; font-size: 0.85rem; background: #111; }
    .flight-list th { text-align: left; color: #FFD700; border-bottom: 2px solid #333; padding: 10px; }
    .flight-list td { padding: 10px; border-bottom: 1px solid #222; }
    .update-btn { background: #FFD700; color: #000; border: none; padding: 20px; width: 100%; font-size: 1.4rem; font-weight: bold; border-radius: 15px; cursor: pointer; margin-top: 15px; }
</style></head>
<body><div class="container">
    <div style="text-align:center;">
        <span class="criteria-badge">情報は15分おきに自動生成・配信中</span>
    </div>
    <div class="rank-box">
        <p class="rank-main">[[RANK]]</p>
        <p style="color:#fff; font-weight:bold; margin:5px 0;">[[RANK_MSG]]</p>
    </div>
    <div class="stand-grid">
        [[CARDS]]
    </div>
    <div class="advice-box">
        <strong>⚡ 戦術アドバイス：</strong><br>[[REASON]]
    </div>
    <h3>✈️ 到着詳細 (直近30分)</h3>
    <table class="flight-list">
        <thead><tr><th>時刻</th><th>便名</th><th>出身</th><th>推計</th></tr></thead>
        <tbody>[[ROWS]]</tbody>
    </table>
    <button class="update-btn" onclick="location.reload()">最新情報に更新</button>
    <div style="text-align:center; font-size:0.75rem; color:#555; margin-top:20px;">最終更新: [[TIME]] | v3.6 Modular</div>
</div></body></html>
"""

def run_render():
    with open(CONFIG["RESULT_JSON"], "r", encoding="utf-8") as f:
        data = json.load(f)
    
    tp = data["total_pax"]
    rk, col, msg = ("🌑 D", "#888", "【撤退】需要なし")
    if tp > 800: rk, col, msg = ("🌈 S", "#FFD700", "【激熱】即出撃！")
    elif tp > 400: rk, col, msg = ("🔥 A", "#FF4500", "【推奨】安定需要")
    elif tp > 100: rk, col, msg = ("✨ B", "#00ff7f", "【注意】小規模")
    
    # ターミナルカード生成
    best_key = max(data["stands"], key=data["stands"].get) if tp > 0 else ""
    cards = ""
    for i, label in enumerate(["1号 (T1南)", "2号 (T1北)", "3号 (T2)", "4号 (T2)", "国際 (T3)"], 1):
        key = f"P{i}"
        is_best = "best-stand" if key == best_key else ""
        is_intl = "intl" if key == "P5" else ""
        cards += f'<div class="stand-card {is_best} {is_intl}"><span class="label">{label}</span><span class="val">{data["stands"][key]}人</span></div>'

    # 行生成
    rows = ""
    for r in data["rows"]:
        rows += f"<tr><td>{r['time']}</td><td>{r['flight']}</td><td>{r['origin']}</td><td>{r['pax']}名</td></tr>"

    html = HTML_TEMPLATE.replace("[[RANK]]", rk).replace("[[RANK_COLOR]]", col).replace("[[RANK_MSG]]", msg) \
        .replace("[[CARDS]]", cards) \
        .replace("[[REASON]]", f"羽田全体で約{tp}名の需要を検知。{best_key.replace('P','')}番付近が有力。") \
        .replace("[[ROWS]]", rows if rows else "<tr><td colspan='4'>対象なし</td></tr>") \
        .replace("[[TIME]]", data["update_time"])

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML Rendered.")

if __name__ == "__main__":
    run_render()
