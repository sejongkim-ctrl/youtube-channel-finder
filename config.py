"""
YouTube Channel Finder Configuration
마케팅 협업 채널 발굴을 위한 YouTube 채널 검색/분석 도구 설정
"""

# 검색 프리셋 키워드
SEARCH_PRESETS = {
    "건강": {"keyword": "건강 채널", "emoji": "💊"},
    "한방": {"keyword": "한방 한의학", "emoji": "🌿"},
    "웰니스": {"keyword": "웰니스 라이프스타일", "emoji": "🧘"},
    "수면": {"keyword": "수면 건강 불면증", "emoji": "😴"},
    "식품": {"keyword": "건강기능식품 리뷰", "emoji": "🥗"},
    "뷰티": {"keyword": "뷰티 피부관리", "emoji": "✨"},
}

# YouTube API 설정
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MAX_SEARCH_RESULTS = 10
MAX_RECENT_VIDEOS = 10

# Gemini API 설정
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_FALLBACK_MODEL = "gemini-1.5-flash"
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_OUTPUT_TOKENS = 4096

# 캐시 설정
CACHE_DIR = "cache"
CACHE_TTL_HOURS = 24

# Flask 설정
FLASK_PORT = 5000
FLASK_DEBUG = True

# 수 브랜드 컨텍스트 (daily-issue-monitor에서 재활용)
SUU_BRAND_CONTEXT = """
# 브랜드 정체성: 수 (Soo)
- 핵심 USP: 한의사 전문성 기반 건강기능식품
- 포지셔닝: 천년 한방 지혜 + 현대 과학 검증
- 차별화: 한의사 직접 처방·감수, 전통 한약재 + 현대 추출 기술, 체질 맞춤형 추천

# 타겟 시장
- 시장 규모: 국내 건강기능식품 시장 7.3조 원 (연평균 8% 성장)
- 타겟 고객: 20~50대 건강 관심층 (얼리 웰니스, 수면 건강, 갱년기 관리)
- 주요 채널: 올리브영, 쿠팡, 자사몰, 한의원 제휴

# 제품 라인업
1. 한방 숙면 플러스 (Phase 1): 20~40대 불면증 타겟
2. 체질 맞춤 유산균 (Phase 2): 전 연령 소화·면역
3. 갱년기 밸런스 (Phase 3): 40~50대 여성

# 주요 트렌드
- 얼리 웰니스: 젊은 세대의 예방적 건강관리
- 수면 건강: 300% 성장 (스트레스, 불면증 증가)
- 퍼스널라이제이션: 체질별 맞춤 솔루션
"""

# 인플루언서 마케팅 평가 기준 (v2 - 이중 축 평가)
INFLUENCER_CONTEXT = """
# 인플루언서 협업 평가 기준 (v2)

## 평가 축 1: 콘텐츠 주제 적합도 (Topic Fit)
건강/웰니스 관련 콘텐츠를 직접 다루는 채널에 적용.
- 건강/한방/웰니스 콘텐츠 비율이 높을수록 유리
- 수면/갱년기/면역/한방 키워드 포함 여부
- 의료 전문가 또는 건강 전문 크리에이터

## 평가 축 2: 행동 맥락 적합도 (Behavioral Context Fit)
건강 콘텐츠가 아니더라도 시청자의 구매 행동을 유도할 수 있는 채널에 적용.
핵심 질문: "이 채널의 시청자가 가족/지인에게 건강 선물을 할 동기가 있는가?"

행동 맥락 지표:
1. **시청자 신뢰도**: 댓글에서 크리에이터를 형/누나/친구처럼 부르는 비율
2. **광고 수용도**: PPL/협찬에 대한 댓글 반응 (거부감 vs 자연스럽다는 반응)
3. **선물 맥락**: 가족/부모 관련 콘텐츠 비율, 명절/기념일 시즌 활용도
4. **감정 온도**: 댓글의 따뜻함/가족애/그리움 감정 비율
5. **인물 애착**: 반복 등장 인물에 대한 시청자 감정 투자 수준

## 필수 요건 (공통)
- 구독자 1만 이상 (마이크로 인플루언서 이상)
- 최근 3개월 내 활동 채널 (휴면 채널 제외)
- 의약품/허위 효능 주장 이력 없음

## 회피 대상
- 극단적 건강법 (단식, 해독 등) 주장 채널
- 경쟁 한방 브랜드 전속 채널
- 식약처 규정 위반 콘텐츠 이력
- 시청자 연령이 10대 중심인 채널

## 실제 전환 사례 (조튜브 케이스)
비건강 채널(People & Blogs)이었지만 구매 전환 최고. 이유:
- 가족 콘텐츠 → 시청자의 "선물하기" 심리 활성화
- 높은 인격적 신뢰 → 광고 거부감 제로
- 명절 시즌 + 가족 영상 + 공진단 PPL = 자연스러운 구매 동선
→ "콘텐츠 주제"가 아닌 "시청자 행동 맥락"이 전환을 만든다
"""

# 통합 분석 프롬프트 v2 (인구통계 + 브랜드 적합도 + 댓글 기반 행동 분석)
COMBINED_ANALYSIS_PROMPT = """당신은 YouTube 인플루언서 마케팅 전문가다.
채널 데이터와 실제 시청자 댓글을 분석하여 (1) 구독자 인구통계 추정과 (2) 수(Soo) 브랜드 적합도를 평가해라.

핵심 원칙: "콘텐츠 주제"뿐 아니라 "시청자 행동 맥락"도 동등하게 평가한다.
건강 채널이 아니더라도, 시청자의 신뢰도·감정 맥락·선물 동기가 높으면 구매 전환이 발생한다.

{brand_context}

{influencer_context}

[채널 정보]
- 채널명: {channel_name}
- 설명: {channel_description}
- 구독자 수: {subscriber_count}
- 총 조회수: {total_views}
- 영상 수: {video_count}
- 개설일: {published_at}
- 국가: {country}

[최근 영상 분석]
{recent_videos_summary}

[시청자 댓글 샘플 (최근 인기 영상 상위 댓글)]
{comments_summary}

중요: strengths와 risks의 각 항목은 반드시 1문장으로 간결하게 작성할 것. 장문 금지.

반드시 아래 JSON 형태로만 응답해라. 서론/결론 없이 JSON만 출력:
{{
  "demographics": {{
    "estimated_age_distribution": {{
      "10대": "N%",
      "20대": "N%",
      "30대": "N%",
      "40대": "N%",
      "50대 이상": "N%"
    }},
    "estimated_gender_ratio": {{
      "남성": "N%",
      "여성": "N%"
    }},
    "primary_interests": ["관심사1", "관심사2", "관심사3"],
    "content_category": "카테고리명",
    "audience_persona": "핵심 시청자를 2~3문장으로 묘사 (댓글 기반)",
    "confidence_level": "high/medium/low"
  }},
  "brand_fit": {{
    "score": 0,
    "grade": "S/A/B/C/D",
    "topic_fit_score": 0,
    "behavioral_fit_score": 0,
    "verdict": "이 채널과 협업해야 하는가에 대한 명확한 결론 1~2문장. 예: '가족 콘텐츠의 높은 신뢰도가 선물 구매를 자연스럽게 유도하므로, 명절 시즌 공진단 PPL에 최적이다.'",
    "strengths": {{
      "audience_match": "시청자-타겟 일치도 1문장 (예: 30~40대 여성 비율 70%로 핵심 타겟과 정확히 일치)",
      "trust_level": "시청자 신뢰 관계 1문장 (예: 댓글에서 언니 호칭 빈도 높고 제품 추천 수용도 우수)",
      "content_synergy": "콘텐츠-브랜드 시너지 1문장 (예: 건강 루틴 콘텐츠가 40%로 한방 제품 노출이 자연스러움)",
      "conversion_potential": "구매 전환 가능성 1문장 (예: 가족 선물 맥락이 강해 명절 시즌 전환율이 높을 것으로 추정)",
      "cost_value": "비용 대비 가치 1문장 (예: 인게이지먼트 대비 CPM 효율이 우수한 마이크로 인플루언서)"
    }},
    "risks": {{
      "audience_mismatch": "시청자-타겟 불일치 1문장 (해당 없으면 '해당 없음')",
      "content_conflict": "콘텐츠 충돌 리스크 1문장 (해당 없으면 '해당 없음')",
      "timing_dependency": "시즌 의존도 1문장 (해당 없으면 '해당 없음')",
      "cost_efficiency": "비용 효율 리스크 1문장 (해당 없으면 '해당 없음')",
      "competitor_exposure": "경쟁사 노출 리스크 1문장 (해당 없으면 '해당 없음')"
    }},
    "collaboration_ideas": ["구체적 협업 아이디어 1", "구체적 협업 아이디어 2", "구체적 협업 아이디어 3"],
    "best_timing": "협업 최적 시기 (예: 추석/설/어버이날)",
    "estimated_cpm": "예상 CPM 범위 (원)",
    "reasoning": "점수 산출 근거 2문장 이내",
    "similar_channel_keywords": ["이 채널과 시청자 행동 맥락이 유사한 채널을 찾기 위한 구체적 검색 키워드 3개 (단일 단어 금지, 2~3단어 조합. 예: 시골부모 브이로그, 40대직장인 건강루틴, 국제커플 일상)"]
  }}
}}

브랜드 적합도 점수 산출 (총 100점):

[축1] 콘텐츠 주제 적합도 (topic_fit_score, 40점 만점)
- 건강/한방/웰니스 콘텐츠 비율 (15점)
- 타겟 연령·성별 일치도 (15점)
- 브랜드 세이프티 (10점)

[축2] 행동 맥락 적합도 (behavioral_fit_score, 40점 만점) — 댓글 분석 기반
- 시청자-크리에이터 신뢰도: 형/누나/친구 호칭, 인격적 교류 수준 (10점)
- 광고 수용도: PPL 관련 댓글의 긍정/부정 비율 (10점)
- 선물/가족 맥락: 가족·부모·명절 관련 감정 비율 (10점)
- 감정 온도: 따뜻함·그리움·행복 감정 비율 (10점)

[공통] 채널 역량 (20점)
- 인게이지먼트: 좋아요/조회 비율 (10점)
- 채널 규모·성장성 (10점)

score = topic_fit_score + behavioral_fit_score + 채널역량점수
등급: S(85+), A(70-84), B(55-69), C(40-54), D(0-39)

규칙:
- strengths와 risks 각 항목은 1문장. 해당 없으면 "해당 없음"
- verdict는 score/grade와 반드시 일관되게 (A등급 → 긍정적 verdict)
- similar_channel_keywords는 "건강", "가족" 같은 단일 단어 금지, 2~3단어 조합 필수
"""

# YouTube 카테고리 ID 매핑
YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
}
