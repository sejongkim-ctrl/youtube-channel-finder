"""
YouTube Channel Finder - Flask Application
마케팅 협업 채널 발굴을 위한 웹 인터페이스
"""

from flask import Flask, render_template, request, jsonify, Response
from youtube_analyzer import YouTubeAnalyzer
from config import SEARCH_PRESETS, FLASK_PORT, FLASK_DEBUG

app = Flask(__name__)
analyzer = YouTubeAnalyzer()


@app.route("/")
def index():
    """메인 페이지"""
    status = analyzer.get_status()
    return render_template("index.html", presets=SEARCH_PRESETS, status=status)


@app.route("/api/search", methods=["POST"])
def api_search():
    """키워드로 채널 검색"""
    data = request.get_json()
    keyword = data.get("keyword", "").strip()
    max_results = data.get("max_results", 10)

    if not keyword:
        return jsonify({"error": "검색어를 입력하세요."}), 400

    result = analyzer.search_channels(keyword, max_results)
    return jsonify(result)


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """채널 URL 또는 ID로 상세 분석"""
    data = request.get_json()
    channel_input = data.get("channel_input", "").strip()

    if not channel_input:
        return jsonify({"error": "채널 URL 또는 ID를 입력하세요."}), 400

    result = analyzer.analyze_channel(channel_input)
    return jsonify(result)


@app.route("/api/export/csv", methods=["POST"])
def api_export_csv():
    """분석 결과 CSV 내보내기"""
    data = request.get_json()
    channels = data.get("channels", [])

    if not channels:
        return jsonify({"error": "내보낼 데이터가 없습니다."}), 400

    csv_content = analyzer.export_csv(channels)
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=youtube_channels.csv"},
    )


@app.route("/api/similar", methods=["POST"])
def api_similar():
    """유사 채널 검색 (키워드 통합 + 적합성 필터링)"""
    data = request.get_json()
    keywords = data.get("keywords", [])
    exclude = data.get("exclude_channel_id", None)
    top_n = data.get("top_n", 5)

    # 하위 호환: 단일 keyword 필드도 지원
    if not keywords and data.get("keyword"):
        keywords = [data["keyword"]]

    if not keywords:
        return jsonify({"error": "검색 키워드가 없습니다."}), 400

    result = analyzer.search_similar_channels(keywords, exclude, top_n)
    return jsonify(result)


@app.route("/api/quota")
def api_quota():
    """API Quota 사용량"""
    status = analyzer.get_status()
    return jsonify(status)


if __name__ == "__main__":
    import os

    status = analyzer.get_status()
    port = int(os.environ.get("PORT", FLASK_PORT))
    debug = os.environ.get("RENDER") is None  # Render 환경이면 debug off

    print("=" * 50)
    print("  YouTube Channel Finder")
    print("=" * 50)
    if not status["youtube_connected"]:
        print("  ⚠️  YouTube API 키 미설정 (.env 파일 확인)")
    else:
        print("  ✅ YouTube API 연결됨")
    if not status["gemini_connected"]:
        print("  ⚠️  Gemini API 키 미설정 (AI 분석 비활성)")
    else:
        print("  ✅ Gemini AI 연결됨")
    print(f"  🌐 http://localhost:{port}")
    print("=" * 50)

    app.run(debug=debug, port=port)
