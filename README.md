# YouTube Channel Finder

마케팅 협업 채널 발굴을 위한 YouTube 채널 검색/분석 웹 도구.
키워드 검색 + 채널 URL 직접 분석, AI 기반 구독자 인구통계 추정, 수(Soo) 브랜드 적합도 평가를 지원한다.

## 설치 및 실행

```bash
cd youtube-channel-finder
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 API 키 입력 후
python app.py
# → http://localhost:5000
```

## API 키 발급

### 1. YouTube Data API v3

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 상단 프로젝트 선택 → "새 프로젝트" → 이름: `youtube-channel-finder` → "만들기"
3. 좌측 메뉴 → "API 및 서비스" → "라이브러리" → "YouTube Data API v3" 검색 → "사용"
4. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보" → "+ 사용자 인증 정보 만들기" → "API 키"
5. 생성된 키 복사 → `.env` 파일의 `YOUTUBE_API_KEY`에 붙여넣기

일일 무료 할당량: 10,000 units (키워드 검색 1회 = 101 units, 채널 분석 1회 = 3 units)

### 2. Google Gemini API

1. [Google AI Studio](https://aistudio.google.com/apikey) 접속
2. "Create API Key" → 키 복사 → `.env` 파일의 `GEMINI_API_KEY`에 붙여넣기

다른 프로젝트(daily-issue-monitor, soo-kin-monitor)와 반드시 별도 키를 사용할 것. 무료 일일 한도 20회.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 키워드 검색 | 건강/한방/웰니스 등 키워드로 채널 탐색 |
| 프리셋 검색 | 6개 프리셋 버튼 (건강, 한방, 웰니스, 수면, 식품, 뷰티) |
| 채널 URL 분석 | @handle, /channel/UCxxxx 등 URL 직접 입력 |
| AI 인구통계 추정 | Gemini가 최근 영상 분석 기반으로 연령/성별/관심사 추정 |
| 브랜드 적합도 | 수 브랜드와의 적합도 0~100 점수 + S/A/B/C/D 등급 |
| CSV 내보내기 | 분석 결과를 CSV 파일로 다운로드 |

## 파일 구조

```
youtube-channel-finder/
├── app.py                  # Flask 서버
├── youtube_analyzer.py     # 핵심 분석 로직
├── config.py               # 설정, 프롬프트, 브랜드 컨텍스트
├── requirements.txt
├── .env / .env.example
├── cache/                  # 분석 결과 캐시 (24시간 유효)
├── templates/index.html    # UI
└── static/
    ├── style.css
    └── app.js
```
