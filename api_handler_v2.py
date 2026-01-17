# ==========================================
# Project: KASETACK - analyzer_v2.py (Logic Restoration Master)
# ==========================================
from datetime import datetime

def analyze_demand(flights):
    """
    v7.7の統計比率（Tさんの重み付け）を完全復元し、
    人数が取れない場合の期待値（150人）を注入する新エンジン。
    """
    
    # 1. Tさんの統計比率（v7.7 継承）
    # [T1南, T1北, T2(3号), T2(4号), T3国際]
    WEIGHT_MASTER = {
        7:[2,0,1,0,8], 8:[8,9,13,4,0], 9:[10,9,16,3,1], 10:[6,8,9,4,0],
        11:[10,10,10,6,1], 12:[9,7,14,4,1], 13:[10,9,8,4,0], 14:[8,5,9,7,0],
        15:[7,7,13,3,0], 16:[7,12,10,5,2], 17:[10,7,10,4,6], 18:[10,8,11,9,1],
        19:[9,7,11,3,1], 20:[11,7,11,4,2], 21:[10,10,14,4,1], 22:[7,7,9,4,2], 23:[1,0,2,3,0]
    }

    # 集計用変数の初期化
    pax_t1, pax_t2, pax_t3 = 0, 0, 0
    now_hour = datetime.now().hour
    w = WEIGHT_MASTER.get(now_hour, [1, 1, 1, 1, 1])

    # 2. フライトデータの解析
    for f in flights:
        # APIに人数データ(pax)がない場合は、期待値「150人」を代入
        pax = f.get('pax') or 150
        term = str(f.get('terminal', ''))

        if '1' in term:
            pax_t1 += pax
        elif '2' in term:
            pax_t2 += pax
        elif '3' in term or 'I' in term:
            pax_t3 += pax
        else:
            # ターミナル不明の場合は、期待値としてT3に振り分け
            pax_t3 += pax

    # 3. Tさんの比率で各乗り場へ分配（期待値計算）
    # 分母が0にならないようガードを入れつつ計算
    t1_total_w = (w[0] + w[1]) or 2
    t2_total_w = (w[2] + w[3] + w[4]) or 3

    results = {
        "1号(T1南)": int(pax_t1 * w[0] / t1_total_w),
        "2号(T1北)": int(pax_t1 * w[1] / t1_total_w),
        "3号(T2)":   int(pax_t2 * w[2] / t2_total_w),
        "4号(T2)":   int(pax_t2 * w[3] / t2_total_w),
        "国際(T3)":  pax_t3 + int(pax_t2 * w[4] / t2_total_w)
    }

    return results