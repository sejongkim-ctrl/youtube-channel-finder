"""
YouTube Channel Finder - Streamlit App
수(Soo) 브랜드 마케팅 협업 채널 발굴
"""

import os
import streamlit as st

# Streamlit secrets → 환경변수 브릿지 (Cloud 배포용)
for key in ["YOUTUBE_API_KEY", "GEMINI_API_KEY"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

from youtube_analyzer import YouTubeAnalyzer
from config import SEARCH_PRESETS

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="YouTube Channel Finder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── 커스텀 CSS ───
st.markdown("""
<style>
.grade-S { color: #ffd700; } .grade-A { color: #22c55e; }
.grade-B { color: #3b82f6; } .grade-C { color: #eab308; } .grade-D { color: #ef4444; }

.score-row { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.score-big { font-size: 48px; font-weight: 800; line-height: 1; }
.grade-big { font-size: 28px; font-weight: 800; padding: 4px 14px; border-radius: 8px; }
.gbg-S { background: rgba(255,215,0,0.2); } .gbg-A { background: rgba(34,197,94,0.2); }
.gbg-B { background: rgba(59,130,246,0.2); } .gbg-C { background: rgba(234,179,8,0.2); }
.gbg-D { background: rgba(239,68,68,0.2); }

.pri-badge { display:inline-block; padding:4px 12px; border-radius:14px; font-size:13px; font-weight:600; }
.pri-urgent { background:rgba(239,68,68,0.15); color:#ef4444; }
.pri-review { background:rgba(234,179,8,0.15); color:#eab308; }
.pri-hold { background:rgba(139,152,165,0.15); color:#8b98a5; }

.verdict-box { padding:14px 18px; border-radius:8px; font-size:15px; line-height:1.6; border-left:4px solid; margin:8px 0 16px; }
.vd-S { background:rgba(255,215,0,0.08); border-color:#ffd700; }
.vd-A { background:rgba(34,197,94,0.08); border-color:#22c55e; }
.vd-B { background:rgba(59,130,246,0.08); border-color:#3b82f6; }
.vd-C { background:rgba(234,179,8,0.08); border-color:#eab308; }
.vd-D { background:rgba(239,68,68,0.08); border-color:#ef4444; }

.sr-item { padding:10px 14px; border-radius:8px; margin-bottom:8px; background:rgba(255,255,255,0.03); }
.s-item { border-left:3px solid #22c55e; } .r-item { border-left:3px solid #ef4444; }
.sr-label { font-weight:600; font-size:13px; margin-bottom:4px; }
.s-label { color:#22c55e; } .r-label { color:#ef4444; }
.sr-detail { color:#8b98a5; font-size:13px; line-height:1.5; }
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


# ─── 헤더 ───
st.title("YouTube Channel Finder")
st.caption("수(Soo) 브랜드 마케팅 협업 채널 발굴")

status = analyzer.get_status()
c1, c2, c3 = st.columns(3)
c1.caption(f"{'✅' if status['youtube_connected'] else '⚠️'} YouTube API")
c2.caption(f"{'✅' if status['gemini_connected'] else '⚠️'} Gemini AI")
c3.caption(f"📊 Quota: {status['quota_used']}")

st.divider()


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


# ─── 탭 ───
tab_search, tab_analyze = st.tabs(["🔍 채널 검색", "📊 채널 분석"])

with tab_search:
    col_in, col_btn = st.columns([5, 1])
    keyword = col_in.text_input("검색", placeholder="건강 채널, 한방 한의학, ...", label_visibility="collapsed", key="search_kw")
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

    if st.session_state.search_results:
        st.subheader(f"검색 결과 ({len(st.session_state.search_results)}개)")
        for ch in st.session_state.search_results:
            cols = st.columns([1, 6, 1])
            cols[0].image(ch.get("thumbnail", ""), width=56)
            with cols[1]:
                st.markdown(f"**{ch['title']}**")
                st.caption(f"구독자 {ch['subscriber_display']} · 영상 {ch['video_count']:,}개 · {ch.get('country', 'N/A')}")
            if cols[2].button("분석", key=f"a_{ch['channel_id']}"):
                run_analysis(ch["channel_id"])

with tab_analyze:
    col_in, col_btn = st.columns([5, 1])
    ch_input = col_in.text_input("분석", placeholder="채널 URL, @핸들, 또는 채널명 입력", label_visibility="collapsed")
    if col_btn.button("분석", key="direct_analyze", type="primary", use_container_width=True):
        if ch_input:
            run_analysis(ch_input)


# ─── 분석 결과 ───
data = st.session_state.analysis_data
if not data:
    st.stop()

st.divider()
hcol1, hcol2 = st.columns([6, 1])
hcol1.header(data.get("title", ""))
if data.get("from_cache"):
    hcol2.caption("📦 캐시")

# 기본 지표
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("구독자", data.get("subscriber_display", "-"))
m2.metric("총 조회수", data.get("view_display", "-"))
m3.metric("영상 수", f"{data.get('video_count', 0):,}개")
m4.metric("국가", data.get("country", "-"))
m5.metric("개설일", data.get("published_at", "")[:10] or "-")

eng = data.get("engagement", {})
if eng.get("avg_views"):
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("평균 조회수", eng["avg_views_display"])
    e2.metric("평균 좋아요", eng["avg_likes_display"])
    e3.metric("조회/구독", f"{eng['view_sub_ratio']}%")
    e4.metric("좋아요/조회", f"{eng['like_view_ratio']}%")

st.divider()

# ─── 인구통계 + 브랜드 적합도 ───
col_demo, col_fit = st.columns(2)

with col_demo:
    st.subheader("인구통계 추정")
    demo = data.get("demographics", {})
    if demo.get("estimated_age_distribution"):
        age = demo["estimated_age_distribution"]
        age_nums = {k: int(v.replace("%", "").strip() or 0) for k, v in age.items()}
        st.bar_chart(age_nums, height=200)

        gender = demo.get("estimated_gender_ratio", {})
        if gender:
            st.markdown(" · ".join(f"**{k}** {v}" for k, v in gender.items()))

        interests = demo.get("primary_interests", [])
        if interests:
            st.caption("관심사: " + " · ".join(interests))

        persona = demo.get("audience_persona", "")
        if persona:
            st.info(persona)

        conf = demo.get("confidence_level", "low")
        conf_label = {"high": "높음", "medium": "보통", "low": "낮음"}.get(conf, conf)
        st.caption(f"추정 신뢰도: {conf_label}")
    else:
        st.info("AI 분석 데이터 없음")

with col_fit:
    st.subheader("브랜드 적합도")
    fit = data.get("brand_fit", {})
    if fit.get("score") is not None:
        g = fit.get("grade", "D")
        s = fit.get("score", 0)
        p = fit.get("priority", "보류")
        pc = "pri-urgent" if "즉시" in p else "pri-review" if "검토" in p else "pri-hold"

        st.markdown(f"""
        <div class="score-row">
            <span class="score-big grade-{g}">{s}</span>
            <span class="grade-big grade-{g} gbg-{g}">{g}</span>
            <span class="pri-badge {pc}">{p}</span>
        </div>
        """, unsafe_allow_html=True)

        verdict = fit.get("verdict", "")
        if verdict:
            st.markdown(f'<div class="verdict-box vd-{g}">{verdict}</div>', unsafe_allow_html=True)

        s1, s2 = st.columns(2)
        s1.metric("콘텐츠 주제", f"{fit.get('topic_fit_score', '-')}/40")
        s2.metric("행동 맥락", f"{fit.get('behavioral_fit_score', '-')}/40")

        timing = fit.get("best_timing", "")
        if timing:
            st.caption(f"최적 협업 시기: **{timing}**")
    else:
        st.info("AI 분석 데이터 없음")

# ─── 강점 / 리스크 ───
if fit.get("score") is not None:
    st.divider()
    SL = {"audience_match":("👥","시청자 일치도"), "trust_level":("🤝","신뢰 관계"),
          "content_synergy":("🎯","콘텐츠 시너지"), "conversion_potential":("💎","전환 가능성"),
          "cost_value":("📊","비용 가치")}
    RL = {"audience_mismatch":("👥","시청자 불일치"), "content_conflict":("⚡","콘텐츠 충돌"),
          "timing_dependency":("📅","시즌 의존도"), "cost_efficiency":("💰","비용 효율"),
          "competitor_exposure":("🔍","경쟁 노출")}

    col_s, col_r = st.columns(2)
    with col_s:
        st.markdown("**강점**")
        strengths = fit.get("strengths", {})
        if isinstance(strengths, dict):
            for k, v in strengths.items():
                if v and v != "해당 없음":
                    ic, lb = SL.get(k, ("+", k))
                    st.markdown(f'<div class="sr-item s-item"><div class="sr-label s-label">{ic} {lb}</div><div class="sr-detail">{v}</div></div>', unsafe_allow_html=True)
        elif isinstance(strengths, list):
            for x in strengths:
                st.markdown(f"+ {x}")

    with col_r:
        st.markdown("**리스크**")
        risks = fit.get("risks", {})
        if isinstance(risks, dict):
            for k, v in risks.items():
                if v and v != "해당 없음":
                    ic, lb = RL.get(k, ("!", k))
                    st.markdown(f'<div class="sr-item r-item"><div class="sr-label r-label">{ic} {lb}</div><div class="sr-detail">{v}</div></div>', unsafe_allow_html=True)
        elif isinstance(risks, list):
            for x in risks:
                st.markdown(f"! {x}")

    # 협업 아이디어 + CPM
    col_i, col_c = st.columns(2)
    with col_i:
        st.markdown("**협업 아이디어**")
        for idea in fit.get("collaboration_ideas", []):
            st.markdown(f"▸ {idea}")
    col_c.metric("예상 CPM", fit.get("estimated_cpm", "N/A"))

    reasoning = fit.get("reasoning", "")
    if reasoning:
        st.caption(reasoning)

    # ─── 유사 채널 ───
    keywords = fit.get("similar_channel_keywords", [])
    if keywords:
        st.divider()
        st.caption(f"유사 채널 키워드: {' · '.join(keywords)}")
        if st.button("유사 채널 탐색"):
            with st.spinner(f"적합 채널 탐색 중... ({len(keywords)}개 키워드 통합 검색)"):
                result = analyzer.search_similar_channels(keywords, exclude_channel_id=data.get("channel_id"), top_n=5)
                if "error" not in result:
                    st.session_state.similar_channels = result
                    st.rerun()
                else:
                    st.error(result["error"])

    similar = st.session_state.similar_channels
    if similar and similar.get("channels"):
        st.subheader(f"유사 채널 추천 ({similar.get('pool_size', 0)}개 후보 중 {len(similar['channels'])}개)")
        for ch in similar["channels"]:
            cols = st.columns([1, 5, 1, 1])
            cols[0].image(ch.get("thumbnail", ""), width=40)
            with cols[1]:
                st.markdown(f"**{ch['title']}**")
                st.caption(f"{ch['subscriber_display']} 구독 · {ch['video_count']:,}개")
            hint = ch.get("fit_hint", "")
            if "높은" in hint:
                cols[2].success(hint)
            elif "보통" in hint:
                cols[2].warning(hint)
            else:
                cols[2].info(hint)
            if cols[3].button("분석", key=f"sim_{ch['channel_id']}"):
                run_analysis(ch["channel_id"])

# ─── 최근 영상 ───
recent = data.get("recent_videos", [])
if recent:
    st.divider()
    with st.expander("최근 영상", expanded=False):
        import pandas as pd
        df = pd.DataFrame([
            {"#": i + 1, "제목": v["title"], "카테고리": v.get("category_name", ""),
             "조회수": v.get("view_display", ""), "좋아요": v.get("like_display", "")}
            for i, v in enumerate(recent)
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

# ─── 사이드바: 내보내기 ───
with st.sidebar:
    st.header("내보내기")
    if data:
        csv = analyzer.export_csv([data])
        st.download_button("📥 CSV 다운로드", csv, "youtube_channels.csv", "text/csv", use_container_width=True)
    st.divider()
    st.caption(f"Quota: {analyzer.get_status()['quota_used']} units")
