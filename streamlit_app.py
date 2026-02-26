"""
YouTube Channel Finder - Streamlit App
수(Soo) 브랜드 마케팅 협업 채널 발굴
"""

import os
import streamlit as st

# Streamlit secrets → 환경변수 브릿지 (Cloud 배포용)
try:
    for key in ["YOUTUBE_API_KEY", "GEMINI_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass  # 로컬 실행 시 .env 사용

from youtube_analyzer import YouTubeAnalyzer
from config import SEARCH_PRESETS, MIN_SUBSCRIBER_COUNT

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="YouTube Channel Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 커스텀 CSS (Flask 스타일 재현) ───
st.markdown("""
<style>
/* ── Streamlit 기본 스타일 오버라이드 ── */
.stApp { background: #0f1419; }
.block-container { padding-top: 2rem; max-width: 1080px; }
header[data-testid="stHeader"] { background: #0f1419; }

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #2f3b47;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 24px;
    color: #8b98a5;
    font-size: 15px;
    border-bottom: 2px solid transparent;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #1d9bf0 !important;
    border-bottom-color: #1d9bf0 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }

/* 버튼 */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: #1d9bf0;
    border: none;
    color: white;
}
.stButton > button[kind="primary"]:hover {
    background: #1a8cd8;
}

/* 인풋 */
div[data-baseweb="input"] > div {
    background: #1e2a3a !important;
    border-color: #2f3b47 !important;
    border-radius: 8px !important;
}
div[data-baseweb="input"] input {
    color: #e7e9ea !important;
}

/* 기본 텍스트/디바이더 */
hr { border-color: #2f3b47 !important; }
.stMarkdown p { color: #e7e9ea; }

/* metric 카드 숨기기 (커스텀으로 대체) */
[data-testid="stMetric"] { display: none; }

/* expander 스타일 */
.streamlit-expanderHeader {
    background: #1a2332 !important;
    border: 1px solid #2f3b47 !important;
    border-radius: 10px !important;
    color: #e7e9ea !important;
}
details[data-testid="stExpander"] {
    background: #1a2332;
    border: 1px solid #2f3b47;
    border-radius: 10px;
}

/* dataframe */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* 사이드바 */
section[data-testid="stSidebar"] {
    background: #1a2332;
}
[data-testid="stSidebar"][aria-expanded="true"] {
    min-width: 320px;
    max-width: 340px;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1rem;
}
/* 사이드바 내 버튼 작게 */
[data-testid="stSidebar"] .stButton > button {
    font-size: 12px;
    padding: 4px 8px;
    height: auto;
    min-height: 32px;
}

/* ── 커스텀 컴포넌트 ── */

/* 상태 바 */
.st-status-bar {
    display: flex; gap: 10px; margin: 8px 0 0;
    flex-wrap: wrap;
}
.st-status-item {
    font-size: 12px; padding: 4px 10px; border-radius: 12px;
    background: #1a2332; border: 1px solid #2f3b47;
}
.st-status-item.ok { color: #22c55e; border-color: #22c55e; }
.st-status-item.warn { color: #ef4444; border-color: #ef4444; }
.st-status-item.info { color: #8b98a5; }

/* 카드 컨테이너 */
.st-card {
    background: #1a2332; border: 1px solid #2f3b47;
    border-radius: 10px; padding: 20px; margin-bottom: 16px;
}
.st-card h3 {
    font-size: 13px; font-weight: 600; color: #8b98a5;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin: 0 0 14px;
}

/* 채널 카드 (검색 결과) */
.ch-card {
    display: flex; gap: 14px; padding: 14px 16px;
    background: #1a2332; border: 1px solid #2f3b47;
    border-radius: 10px; margin-bottom: 10px;
    align-items: center; transition: border-color 0.2s;
}
.ch-card:hover { border-color: #1d9bf0; }
.ch-avatar {
    width: 48px; height: 48px; border-radius: 50%;
    flex-shrink: 0; object-fit: cover;
}
.ch-info { flex: 1; min-width: 0; }
.ch-name {
    font-size: 15px; font-weight: 600; color: #e7e9ea;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ch-stats {
    display: flex; gap: 12px; margin-top: 3px;
    font-size: 13px; color: #536471;
}

/* 지표 그리드 */
.metrics-row {
    display: flex; gap: 12px; margin-bottom: 12px;
}
.metric-item {
    flex: 1; background: #1a2332; border: 1px solid #2f3b47;
    border-radius: 8px; padding: 14px 16px; text-align: center;
}
.metric-label {
    font-size: 12px; color: #8b98a5; margin-bottom: 4px;
}
.metric-value {
    font-size: 18px; font-weight: 700; color: #e7e9ea;
}
.metric-value.sm { font-size: 15px; }

/* 2컬럼 그리드 */
.grid-2 {
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
}
@media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }

/* 연령/성별 바 */
.demo-bar {
    display: flex; align-items: center; gap: 8px;
    padding: 3px 0; font-size: 13px;
}
.demo-bar-label {
    width: 55px; color: #8b98a5; flex-shrink: 0; font-size: 13px;
}
.demo-bar-fill {
    height: 16px; border-radius: 3px; min-width: 2px;
    transition: width 0.3s;
}
.demo-bar-fill.age { background: #1d9bf0; }
.demo-bar-fill.male { background: #3b82f6; }
.demo-bar-fill.female { background: #ef4444; }
.demo-bar-pct {
    font-size: 12px; color: #536471; width: 36px;
    text-align: right; flex-shrink: 0;
}

/* 관심사 태그 */
.interest-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.interest-tag {
    padding: 4px 10px; background: rgba(29,155,240,0.15);
    border: 1px solid rgba(29,155,240,0.3); border-radius: 14px;
    font-size: 13px; color: #1d9bf0;
}

/* 페르소나 */
.persona-text {
    font-size: 14px; color: #e7e9ea; line-height: 1.6;
    margin-top: 10px; padding: 10px 14px; background: #0f1419;
    border-radius: 8px;
}

/* 신뢰도 배지 */
.conf-badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 11px; font-weight: 600; margin-top: 10px;
}
.conf-high { background: rgba(34,197,94,0.15); color: #22c55e; }
.conf-medium { background: rgba(234,179,8,0.15); color: #eab308; }
.conf-low { background: rgba(239,68,68,0.15); color: #ef4444; }

/* 브랜드 적합도 */
.brand-header {
    display: flex; align-items: center; gap: 16px; margin-bottom: 12px;
}
.score-big {
    font-size: 48px; font-weight: 800; line-height: 1;
}
.grade-badge {
    font-size: 28px; font-weight: 800; padding: 4px 14px; border-radius: 8px;
}
.pri-badge {
    display: inline-block; padding: 4px 12px; border-radius: 14px;
    font-size: 13px; font-weight: 600;
}

/* 등급 색상 */
.gc-S { color: #ffd700; } .gc-A { color: #22c55e; }
.gc-B { color: #3b82f6; } .gc-C { color: #eab308; } .gc-D { color: #ef4444; }
.gbg-S { background: rgba(255,215,0,0.2); } .gbg-A { background: rgba(34,197,94,0.2); }
.gbg-B { background: rgba(59,130,246,0.2); } .gbg-C { background: rgba(234,179,8,0.2); }
.gbg-D { background: rgba(239,68,68,0.2); }

.pri-urgent { background: rgba(239,68,68,0.15); color: #ef4444; }
.pri-review { background: rgba(234,179,8,0.15); color: #eab308; }
.pri-hold { background: rgba(139,152,165,0.15); color: #8b98a5; }

/* verdict 박스 */
.verdict-box {
    padding: 14px 18px; border-radius: 8px; font-size: 15px;
    font-weight: 500; line-height: 1.6; border-left: 4px solid;
    margin: 8px 0 16px; color: #e7e9ea;
}
.vd-S { background: rgba(255,215,0,0.08); border-color: #ffd700; }
.vd-A { background: rgba(34,197,94,0.08); border-color: #22c55e; }
.vd-B { background: rgba(59,130,246,0.08); border-color: #3b82f6; }
.vd-C { background: rgba(234,179,8,0.08); border-color: #eab308; }
.vd-D { background: rgba(239,68,68,0.08); border-color: #ef4444; }

/* 축별 점수 */
.axis-row {
    display: flex; gap: 12px; margin: 12px 0;
}
.axis-box {
    flex: 1; background: #0f1419; border-radius: 8px;
    padding: 10px 14px; display: flex;
    justify-content: space-between; align-items: center;
}
.axis-label { font-size: 13px; color: #8b98a5; }
.axis-val {
    font-size: 20px; font-weight: 700; color: #1d9bf0;
}
.axis-val small { font-size: 12px; color: #536471; font-weight: 400; }

/* 타이밍 */
.timing-box {
    padding: 8px 14px; background: rgba(29,155,240,0.1);
    border-radius: 6px; font-size: 13px; color: #8b98a5;
    margin-bottom: 12px;
}
.timing-box strong { color: #1d9bf0; }

/* 강점/리스크 아이템 */
.sr-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 14px; }
@media (max-width: 768px) { .sr-grid { grid-template-columns: 1fr; } }
.sr-col-title { font-size: 13px; color: #536471; margin-bottom: 8px; font-weight: 600; }
.sr-item {
    background: #0f1419; border-radius: 8px; padding: 10px 14px;
    margin-bottom: 8px;
}
.s-item { border-left: 3px solid #22c55e; }
.r-item { border-left: 3px solid #ef4444; }
.sr-head {
    display: flex; align-items: center; gap: 6px; margin-bottom: 3px;
}
.sr-icon { font-size: 14px; }
.sr-label { font-size: 13px; font-weight: 600; }
.s-label { color: #22c55e; }
.r-label { color: #ef4444; }
.sr-detail { font-size: 13px; color: #8b98a5; line-height: 1.5; }

/* 협업/CPM 그리드 */
.extras-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 16px; margin-top: 16px;
}
@media (max-width: 768px) { .extras-grid { grid-template-columns: 1fr; } }
.extras-title { font-size: 13px; color: #536471; margin-bottom: 6px; font-weight: 600; }
.idea-item { padding: 3px 0; font-size: 14px; color: #e7e9ea; }
.idea-item::before { content: "▸ "; color: #1d9bf0; }
.cpm-val { font-size: 14px; color: #e7e9ea; margin-top: 4px; }
.reasoning-box {
    margin-top: 12px; padding: 10px 14px;
    background: #0f1419; border-radius: 6px;
    font-size: 13px; color: #8b98a5; line-height: 1.6;
}

/* 유사 채널 키워드 */
.sim-keywords {
    margin-top: 16px; padding-top: 12px;
    border-top: 1px solid #2f3b47;
    font-size: 13px; color: #536471;
}

/* 유사 채널 카드 */
.sim-card {
    display: flex; gap: 12px; padding: 12px;
    background: #0f1419; border-radius: 8px;
    align-items: center; margin-bottom: 8px;
    transition: background 0.2s;
}
.sim-card:hover { background: #1e2a3a; }
.sim-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    flex-shrink: 0; object-fit: cover;
}
.sim-info { flex: 1; min-width: 0; }
.sim-name {
    font-size: 14px; font-weight: 600; color: #e7e9ea;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sim-stats {
    display: flex; gap: 12px; font-size: 12px; color: #536471; margin-top: 2px;
}
.fit-badge {
    padding: 2px 8px; border-radius: 10px;
    font-size: 11px; font-weight: 600;
}
.fit-high { background: rgba(34,197,94,0.15); color: #22c55e; }
.fit-medium { background: rgba(234,179,8,0.15); color: #eab308; }
.fit-low { background: rgba(139,152,165,0.15); color: #8b98a5; }

/* 영상 테이블 */
.vid-table {
    width: 100%; border-collapse: collapse; font-size: 14px;
}
.vid-table th {
    text-align: left; padding: 8px 12px; font-size: 12px;
    color: #536471; border-bottom: 1px solid #2f3b47;
    font-weight: 600; text-transform: uppercase;
}
.vid-table td {
    padding: 10px 12px; border-bottom: 1px solid #2f3b47; color: #e7e9ea;
}
.vid-table tr:hover { background: #0f1419; }
.vid-title {
    max-width: 400px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.vid-stat { color: #8b98a5; text-align: right; }
</style>
""", unsafe_allow_html=True)


# ─── 초기화 ───
@st.cache_resource
def get_analyzer():
    return YouTubeAnalyzer()

analyzer = get_analyzer()

for k in ["search_results", "analysis_data", "similar_channels"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k == "search_results" else None


# ─── 헤더 (HTML) ───
status = analyzer.get_status()
yt_cls = "ok" if status["youtube_connected"] else "warn"
gm_cls = "ok" if status["gemini_connected"] else "warn"
yt_txt = "YouTube API 연결됨" if status["youtube_connected"] else "YouTube API 미연결"
gm_txt = "Gemini AI 활성" if status["gemini_connected"] else "Gemini AI 비활성"

st.markdown(f"""
<h1 style="font-size:24px;font-weight:700;color:#e7e9ea;margin:0;">YouTube Channel Finder</h1>
<p style="font-size:14px;color:#8b98a5;margin:4px 0 0;">수(Soo) 브랜드 마케팅 협업 채널 분석 도구</p>
<div class="st-status-bar">
    <span class="st-status-item {yt_cls}">{yt_txt}</span>
    <span class="st-status-item {gm_cls}">{gm_txt}</span>
    <span class="st-status-item info">Quota: {status['quota_used']}/10,000</span>
    <span class="st-status-item info">필터: 구독자 {MIN_SUBSCRIBER_COUNT:,}+ | v2.4</span>
</div>
""", unsafe_allow_html=True)


# ─── 분석 실행 함수 ───
def run_analysis(channel_input):
    with st.spinner("채널 분석 중... (AI 분석에 10~20초 소요)"):
        result = analyzer.analyze_channel(channel_input)
        if "error" in result:
            st.error(result["error"])
        else:
            st.session_state.analysis_data = result
            st.session_state.similar_channels = None
            st.rerun()


# ─── HTML 이스케이프 ───
def esc(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ─── 탭 ───
tab_search, tab_analyze = st.tabs(["키워드 검색", "URL 분석"])

with tab_search:
    col_in, col_btn = st.columns([5, 1])
    keyword = col_in.text_input("검색", placeholder="채널 키워드를 입력하세요 (예: 건강, 한방, 웰니스)", label_visibility="collapsed", key="search_kw")
    search_clicked = col_btn.button("검색", type="primary", use_container_width=True)

    preset_cols = st.columns(len(SEARCH_PRESETS))
    for i, (name, info) in enumerate(SEARCH_PRESETS.items()):
        if preset_cols[i].button(f"{info['emoji']} {name}", use_container_width=True, key=f"pre_{name}"):
            st.session_state["_preset_kw"] = info["keyword"]
            search_clicked = True

    kw = st.session_state.get("_preset_kw", keyword)
    if search_clicked and kw:
        with st.spinner(f"'{kw}' 검색 중..."):
            result = analyzer.search_channels(kw)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.search_results = result.get("channels", [])
        st.session_state.pop("_preset_kw", None)

with tab_analyze:
    col_in, col_btn = st.columns([5, 1])
    ch_input = col_in.text_input("분석", placeholder="채널 URL 또는 @handle 입력", label_visibility="collapsed")
    st.markdown('<p style="font-size:13px;color:#536471;margin-top:-8px;">지원 형식: youtube.com/@handle, youtube.com/channel/UCxxxx, @handle</p>', unsafe_allow_html=True)
    if col_btn.button("분석", key="direct_analyze", type="primary", use_container_width=True):
        if ch_input:
            run_analysis(ch_input)


# ─── Sidebar: 검색 결과 리스트 ───
with st.sidebar:
    channels = st.session_state.search_results
    sidebar_data = st.session_state.analysis_data

    if channels:
        st.markdown(f'<div style="font-size:15px;font-weight:600;color:#e7e9ea;margin-bottom:10px;">검색 결과 ({len(channels)}개)</div>', unsafe_allow_html=True)
        for ch in channels:
            is_active = bool(sidebar_data and sidebar_data.get("channel_id") == ch["channel_id"])
            border_c = "#1d9bf0" if is_active else "#2f3b47"
            bg_c = "#1e2a3a" if is_active else "#1a2332"
            thumb = ch.get("thumbnail", "")
            title_t = esc(ch.get("title", ""))
            subs_d = ch.get("subscriber_display", "")
            vids_n = ch.get("video_count", 0)

            st.markdown(f"""
            <div style="display:flex;gap:10px;padding:10px;background:{bg_c};border:1px solid {border_c};border-radius:8px;margin-bottom:4px;align-items:center;">
                <img src="{thumb}" style="width:36px;height:36px;border-radius:50%;flex-shrink:0;object-fit:cover;" onerror="this.style.display='none'">
                <div style="flex:1;min-width:0;">
                    <div style="font-size:13px;font-weight:600;color:#e7e9ea;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{title_t}</div>
                    <div style="font-size:11px;color:#536471;">구독 {subs_d} · {vids_n:,}개</div>
                </div>
            </div>""", unsafe_allow_html=True)

            if st.button("✓ 분석됨" if is_active else "분석", key=f"a_{ch['channel_id']}", disabled=is_active, use_container_width=True):
                run_analysis(ch["channel_id"])

    st.divider()
    if sidebar_data:
        csv = analyzer.export_csv([sidebar_data])
        st.download_button("CSV 다운로드", csv, "youtube_channels.csv", "text/csv", use_container_width=True)
    st.caption(f"Quota: {analyzer.get_status()['quota_used']} units")


# ─── Main: 분석 결과 (상단 배치) ───
data = st.session_state.analysis_data
if not data:
    if not st.session_state.search_results:
        st.markdown('<p style="color:#536471;text-align:center;padding:60px 0;font-size:15px;">키워드 검색 또는 URL 입력으로 시작하세요</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#536471;text-align:center;padding:40px 0;font-size:15px;">← 좌측 검색 결과에서 채널을 선택하면 분석 결과가 여기에 표시됩니다</p>', unsafe_allow_html=True)
    st.stop()

st.markdown('<hr style="border:1px solid #2f3b47;margin:12px 0 16px;">', unsafe_allow_html=True)

# 채널 제목
cache_html = '<span style="font-size:11px;padding:2px 8px;background:#1a2332;border:1px solid #536471;border-radius:10px;color:#536471;margin-left:10px;">캐시</span>' if data.get("from_cache") else ""
st.markdown(f'<h2 style="font-size:20px;font-weight:700;color:#e7e9ea;margin:0 0 16px;">{esc(data.get("title", ""))}{cache_html}</h2>', unsafe_allow_html=True)

# ─── 기본 지표 (HTML 그리드) ───
eng = data.get("engagement", {})
metrics_html = f"""
<div class="metrics-row">
    <div class="metric-item"><div class="metric-label">구독자</div><div class="metric-value">{data.get('subscriber_display', '-')}</div></div>
    <div class="metric-item"><div class="metric-label">총 조회수</div><div class="metric-value">{data.get('view_display', '-')}</div></div>
    <div class="metric-item"><div class="metric-label">영상 수</div><div class="metric-value">{data.get('video_count', 0):,}개</div></div>
    <div class="metric-item"><div class="metric-label">국가</div><div class="metric-value">{data.get('country', '-')}</div></div>
    <div class="metric-item"><div class="metric-label">개설일</div><div class="metric-value">{(data.get('published_at', '') or '')[:10] or '-'}</div></div>
</div>
"""
if eng.get("avg_views"):
    metrics_html += f"""
<div class="metrics-row">
    <div class="metric-item"><div class="metric-label">평균 조회수</div><div class="metric-value sm">{eng['avg_views_display']}</div></div>
    <div class="metric-item"><div class="metric-label">평균 좋아요</div><div class="metric-value sm">{eng['avg_likes_display']}</div></div>
    <div class="metric-item"><div class="metric-label">조회/구독</div><div class="metric-value sm">{eng['view_sub_ratio']}%</div></div>
    <div class="metric-item"><div class="metric-label">좋아요/조회</div><div class="metric-value sm">{eng['like_view_ratio']}%</div></div>
</div>
"""
st.markdown(metrics_html, unsafe_allow_html=True)

# ─── 인구통계 + 브랜드 적합도 (2컬럼) ───
demo = data.get("demographics", {})
fit = data.get("brand_fit", {})

# 인구통계 카드 HTML
demo_html = '<div class="st-card"><h3>추정 인구통계</h3>'
if demo.get("estimated_age_distribution"):
    age = demo["estimated_age_distribution"]
    demo_html += '<div style="margin-bottom:14px;"><div style="font-size:13px;color:#536471;margin-bottom:6px;">연령 분포 (추정)</div>'
    for k, v in age.items():
        num = int(str(v).replace("%", "").strip() or 0)
        demo_html += f'<div class="demo-bar"><span class="demo-bar-label">{esc(k)}</span><div class="demo-bar-fill age" style="width:{num * 2}px"></div><span class="demo-bar-pct">{esc(v)}</span></div>'
    demo_html += '</div>'

    gender = demo.get("estimated_gender_ratio", {})
    if gender:
        demo_html += '<div style="margin-bottom:14px;"><div style="font-size:13px;color:#536471;margin-bottom:6px;">성별 비율 (추정)</div>'
        for k, v in gender.items():
            num = int(str(v).replace("%", "").strip() or 0)
            fill_cls = "male" if "남" in k else "female"
            demo_html += f'<div class="demo-bar"><span class="demo-bar-label">{esc(k)}</span><div class="demo-bar-fill {fill_cls}" style="width:{num * 2}px"></div><span class="demo-bar-pct">{esc(v)}</span></div>'
        demo_html += '</div>'

    interests = demo.get("primary_interests", [])
    if interests:
        demo_html += '<div style="font-size:13px;color:#536471;margin-bottom:6px;">주요 관심사</div><div class="interest-tags">'
        for i in interests:
            demo_html += f'<span class="interest-tag">{esc(i)}</span>'
        demo_html += '</div>'

    persona = demo.get("audience_persona", "")
    if persona:
        demo_html += f'<div style="font-size:13px;color:#536471;margin:14px 0 6px;">시청자 페르소나</div><div class="persona-text">{esc(persona)}</div>'

    conf = demo.get("confidence_level", "low")
    conf_cls = {"high": "conf-high", "medium": "conf-medium", "low": "conf-low"}.get(conf, "conf-low")
    conf_txt = {"high": "높음", "medium": "보통", "low": "낮음"}.get(conf, conf)
    demo_html += f'<span class="conf-badge {conf_cls}">추정 신뢰도: {conf_txt}</span>'
else:
    demo_html += '<p style="color:#536471;font-size:14px;text-align:center;padding:20px;">AI 분석 데이터 없음</p>'
demo_html += '</div>'

# 브랜드 적합도 카드 HTML
fit_html = '<div class="st-card"><h3>브랜드 적합도</h3>'
if fit.get("score") is not None:
    g = fit.get("grade", "D")
    s = fit.get("score", 0)
    p = fit.get("priority", "보류")
    pc = "pri-urgent" if "즉시" in p else "pri-review" if "검토" in p else "pri-hold"

    fit_html += f"""
    <div class="brand-header">
        <span class="score-big gc-{g}">{s}</span>
        <span class="grade-badge gc-{g} gbg-{g}">{g}</span>
        <span class="pri-badge {pc}">{p}</span>
    </div>"""

    verdict = fit.get("verdict", "")
    if verdict:
        fit_html += f'<div class="verdict-box vd-{g}">{esc(verdict)}</div>'

    topic = fit.get("topic_fit_score", "-")
    behav = fit.get("behavioral_fit_score", "-")
    cap = fit.get("channel_capability_score", "-")
    fit_html += f"""
    <div class="axis-row">
        <div class="axis-box"><span class="axis-label">주제 적합</span><span class="axis-val">{topic}<small>/25</small></span></div>
        <div class="axis-box"><span class="axis-label">행동 맥락</span><span class="axis-val">{behav}<small>/45</small></span></div>
        <div class="axis-box"><span class="axis-label">채널 역량</span><span class="axis-val">{cap}<small>/30</small></span></div>
    </div>"""

    timing = fit.get("best_timing", "")
    if timing:
        fit_html += f'<div class="timing-box">최적 협업 시기: <strong>{esc(timing)}</strong></div>'
else:
    fit_html += '<p style="color:#536471;font-size:14px;text-align:center;padding:20px;">AI 분석 데이터 없음</p>'
fit_html += '</div>'

st.markdown(f'<div class="grid-2">{demo_html}{fit_html}</div>', unsafe_allow_html=True)

# ─── 채널 건강도 ───
health = data.get("channel_health", {})
if health.get("score") is not None and health.get("grade") != "N/A":
    hg = health["grade"]
    hs = health["score"]
    health_html = f"""
    <div class="st-card">
        <h3>채널 건강도</h3>
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px;">
            <span class="score-big gc-{hg}">{hs}</span>
            <span class="grade-badge gc-{hg} gbg-{hg}">{hg}</span>
        </div>
        <div class="axis-row">
            <div class="axis-box">
                <span class="axis-label">업로드 빈도</span>
                <span style="font-size:13px;color:#e7e9ea;">{esc(health.get('upload_frequency', '-'))}</span>
            </div>
            <div class="axis-box">
                <span class="axis-label">숏폼 비율</span>
                <span style="font-size:13px;color:#e7e9ea;">{esc(health.get('shorts_label', '-'))}</span>
            </div>
            <div class="axis-box">
                <span class="axis-label">조회수 추세</span>
                <span style="font-size:13px;color:#e7e9ea;">{esc(health.get('view_trend', '-'))}</span>
            </div>
        </div>
    </div>"""
    st.markdown(health_html, unsafe_allow_html=True)

# ─── 강점 / 리스크 ───
if fit.get("score") is not None:
    SL = {"gift_motivation": ("🎁", "선물 구매 동기"), "trust_transfer": ("🤝", "신뢰 전이력"),
          "premium_fit": ("💎", "프리미엄 적합"), "content_synergy": ("🎯", "콘텐츠 시너지"),
          "seasonal_fit": ("📅", "시즌 활용도")}
    RL = {"audience_mismatch": ("👥", "시청자 불일치"), "content_conflict": ("⚡", "콘텐츠 충돌"),
          "premium_gap": ("💰", "프리미엄 괴리"), "trust_risk": ("🔒", "신뢰도 리스크"),
          "competitor_exposure": ("🔍", "경쟁 노출")}

    sr_html = '<div class="st-card"><div class="sr-grid"><div><div class="sr-col-title">강점</div>'
    strengths = fit.get("strengths", {})
    if isinstance(strengths, dict):
        for k, v in strengths.items():
            if v and v != "해당 없음":
                ic, lb = SL.get(k, ("+", k))
                sr_html += f'<div class="sr-item s-item"><div class="sr-head"><span class="sr-icon">{ic}</span><span class="sr-label s-label">{lb}</span></div><div class="sr-detail">{esc(v)}</div></div>'
    elif isinstance(strengths, list):
        for x in strengths:
            sr_html += f'<div class="sr-item s-item"><div class="sr-detail">+ {esc(x)}</div></div>'

    sr_html += '</div><div><div class="sr-col-title">리스크</div>'
    risks = fit.get("risks", {})
    if isinstance(risks, dict):
        for k, v in risks.items():
            if v and v != "해당 없음":
                ic, lb = RL.get(k, ("!", k))
                sr_html += f'<div class="sr-item r-item"><div class="sr-head"><span class="sr-icon">{ic}</span><span class="sr-label r-label">{lb}</span></div><div class="sr-detail">{esc(v)}</div></div>'
    elif isinstance(risks, list):
        for x in risks:
            sr_html += f'<div class="sr-item r-item"><div class="sr-detail">! {esc(x)}</div></div>'
    sr_html += '</div></div>'

    # 협업 아이디어 + CPM
    ideas = fit.get("collaboration_ideas", [])
    cpm = fit.get("estimated_cpm", "N/A")
    sr_html += '<div class="extras-grid"><div><div class="extras-title">협업 아이디어</div>'
    for idea in ideas:
        sr_html += f'<div class="idea-item">{esc(idea)}</div>'
    sr_html += f'</div><div><div class="extras-title">예상 CPM</div><div class="cpm-val">{esc(cpm)}</div></div></div>'

    reasoning = fit.get("reasoning", "")
    if reasoning:
        sr_html += f'<div class="reasoning-box">{esc(reasoning)}</div>'

    # 유사 채널 키워드
    keywords = fit.get("similar_channel_keywords", [])
    if keywords:
        kw_text = " · ".join(esc(k) for k in keywords)
        sr_html += f'<div class="sim-keywords">유사 채널 키워드: {kw_text}</div>'

    sr_html += '</div>'
    st.markdown(sr_html, unsafe_allow_html=True)

    # 유사 채널 탐색 버튼 (Streamlit 인터렉션)
    if keywords:
        if st.button("유사 채널 탐색"):
            with st.spinner(f"적합 채널 탐색 중... ({len(keywords)}개 키워드 통합 검색)"):
                result = analyzer.search_similar_channels(keywords, exclude_channel_id=data.get("channel_id"), top_n=5)
                if "error" not in result:
                    st.session_state.similar_channels = result
                    st.rerun()
                else:
                    st.error(result["error"])

    # 유사 채널 결과
    similar = st.session_state.similar_channels
    if similar and similar.get("channels"):
        st.markdown(
            f'<div class="st-card"><h3>유사 채널 추천 <span style="font-size:12px;color:#536471;font-weight:400;">'
            f'{similar.get("pool_size", 0)}개 후보 중 상위 {len(similar["channels"])}개</span></h3></div>',
            unsafe_allow_html=True,
        )
        for ch in similar["channels"]:
            hint = ch.get("fit_hint", "")
            fit_cls = "fit-high" if "높은" in hint else "fit-medium" if "보통" in hint else "fit-low"
            reason = ch.get("fit_reason", "")

            col_info, col_btn = st.columns([5, 1])
            with col_info:
                card_html = f"""<div class="sim-card" style="margin-bottom:0">
                    <img src="{ch.get('thumbnail', '')}" class="sim-avatar" onerror="this.style.display='none'">
                    <div class="sim-info">
                        <div class="sim-name">{esc(ch['title'])}</div>
                        <div class="sim-stats">
                            <span>{ch['subscriber_display']} 구독</span>
                            <span>{ch['video_count']:,}개 영상</span>
                            <span class="fit-badge {fit_cls}">{esc(hint)}</span>
                        </div>
                        <div style="font-size:11px;color:#8b98a5;margin-top:2px">{esc(reason)}</div>
                    </div>
                </div>"""
                st.markdown(card_html, unsafe_allow_html=True)
            with col_btn:
                if st.button("분석", key=f"sim_{ch['channel_id']}"):
                    run_analysis(ch["channel_id"])

# ─── 최근 영상 ───
recent = data.get("recent_videos", [])
if recent:
    with st.expander("최근 영상 TOP 10", expanded=False):
        vid_html = '<table class="vid-table"><thead><tr><th>#</th><th>제목</th><th>카테고리</th><th style="text-align:right">조회수</th><th style="text-align:right">좋아요</th></tr></thead><tbody>'
        for i, v in enumerate(recent):
            vid_html += f"""<tr>
                <td style="color:#536471">{i + 1}</td>
                <td class="vid-title">{esc(v['title'])}</td>
                <td style="color:#8b98a5;font-size:12px">{esc(v.get('category_name', ''))}</td>
                <td class="vid-stat">{v.get('view_display', '')}</td>
                <td class="vid-stat">{v.get('like_display', '')}</td>
            </tr>"""
        vid_html += '</tbody></table>'
        st.markdown(vid_html, unsafe_allow_html=True)
