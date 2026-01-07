CONFIG = {
    # ターゲット：Flightradar24 羽田到着便
    "TARGET_URL": "https://www.flightradar24.com/data/airports/hnd/arrivals",
    
    # 取得した生データの保存先
    "DATA_FILE": "haneda_raw.html",
    
    # 解析結果の保存先（renderer.pyとの整合性をとりました）
    "RESULT_FILE": "analysis_result.json",
    "RESULT_JSON": "analysis_result.json",
    
    # HTMLレポートの出力先
    "REPORT_FILE": "index.html"
}
