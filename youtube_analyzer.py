"""
YouTube Channel Analyzer
채널 검색, 상세 분석, AI 인구통계 추정, 브랜드 적합도 평가
"""

import os
import re
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
import google.generativeai as genai

from config import (
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    MAX_SEARCH_RESULTS,
    MAX_RECENT_VIDEOS,
    MIN_SUBSCRIBER_COUNT,
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_OUTPUT_TOKENS,
    CACHE_DIR,
    CACHE_TTL_HOURS,
    COMBINED_ANALYSIS_PROMPT,
    SUU_BRAND_CONTEXT,
    INFLUENCER_CONTEXT,
    YOUTUBE_CATEGORIES,
    CATEGORY_BENCHMARKS,
)

load_dotenv(override=True)


class YouTubeAnalyzer:
    """YouTube 채널 검색 및 분석"""

    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # YouTube API 클라이언트
        self.youtube = None
        if self.youtube_api_key:
            self.youtube = build(
                YOUTUBE_API_SERVICE_NAME,
                YOUTUBE_API_VERSION,
                developerKey=self.youtube_api_key,
            )

        # Gemini AI
        self.model = None
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            try:
                self.model = genai.GenerativeModel(GEMINI_MODEL)
            except Exception:
                self.model = genai.GenerativeModel(GEMINI_FALLBACK_MODEL)

        # 캐시 디렉토리
        self.cache_dir = Path(CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)

        # Quota 트래커
        self._quota_used = 0
        self._quota_reset_date = datetime.now().date()

    def get_status(self):
        """API 연결 상태 반환"""
        return {
            "youtube_connected": self.youtube is not None,
            "gemini_connected": self.model is not None,
            "quota_used": self._quota_used,
        }

    def _track_quota(self, units):
        """YouTube API quota 사용량 추적"""
        today = datetime.now().date()
        if today != self._quota_reset_date:
            self._quota_used = 0
            self._quota_reset_date = today
        self._quota_used += units

    # ─── 검색 ───

    def search_channels(self, keyword, max_results=None):
        """키워드로 YouTube 채널 검색"""
        if not self.youtube:
            return {"error": "YouTube API 키가 설정되지 않았습니다."}

        max_results = max_results or MAX_SEARCH_RESULTS
        # over-fetch: 구독자 필터 후에도 충분한 결과를 확보하기 위해 3배 요청
        fetch_count = min(max_results * 3, 50)

        try:
            # search.list (100 units)
            search_response = (
                self.youtube.search()
                .list(
                    q=keyword,
                    type="channel",
                    part="snippet",
                    maxResults=fetch_count,
                    order="relevance",
                )
                .execute()
            )
            self._track_quota(100)

            channel_ids = [
                item["snippet"]["channelId"]
                for item in search_response.get("items", [])
            ]

            if not channel_ids:
                return {"channels": [], "total": 0}

            # channels.list 배치 호출 (1 unit)
            channels_response = (
                self.youtube.channels()
                .list(
                    id=",".join(channel_ids),
                    part="snippet,statistics,brandingSettings",
                )
                .execute()
            )
            self._track_quota(1)

            channels = []
            for item in channels_response.get("items", []):
                ch = self._parse_channel_data(item)
                subs = ch["subscriber_count"]
                if not isinstance(subs, int) or subs < MIN_SUBSCRIBER_COUNT:
                    continue
                channels.append(ch)

            # 구독자 수 내림차순 정렬 후 max_results개 반환
            channels.sort(key=lambda c: c["subscriber_count"], reverse=True)
            channels = channels[:max_results]

            return {"channels": channels, "total": len(channels)}

        except Exception as e:
            return {"error": f"검색 실패: {str(e)}"}

    # ─── 채널 분석 ───

    def analyze_channel(self, channel_input):
        """채널 URL 또는 ID로 상세 분석"""
        if not self.youtube:
            return {"error": "YouTube API 키가 설정되지 않았습니다."}

        # URL에서 채널 식별자 추출
        channel_id = self._parse_channel_url(channel_input)
        if not channel_id:
            return {"error": "유효하지 않은 채널 URL입니다."}

        # 캐시 확인
        cached = self._load_cache(channel_id)
        if cached:
            cached["from_cache"] = True
            return cached

        try:
            # 1. 채널 기본 정보 (1 unit)
            channel_response = (
                self.youtube.channels()
                .list(
                    id=channel_id,
                    part="snippet,statistics,contentDetails,brandingSettings",
                )
                .execute()
            )
            self._track_quota(1)

            items = channel_response.get("items", [])
            if not items:
                return {"error": "채널을 찾을 수 없습니다."}

            channel_data = self._parse_channel_data(items[0])

            # 2. 최근 영상 수집
            uploads_playlist_id = (
                items[0]
                .get("contentDetails", {})
                .get("relatedPlaylists", {})
                .get("uploads")
            )
            recent_videos = []
            if uploads_playlist_id:
                recent_videos = self._get_recent_videos(uploads_playlist_id)

            channel_data["recent_videos"] = recent_videos

            # 3. AI 분석 (인구통계 + 브랜드 적합도)
            if self.model and recent_videos:
                ai_analysis = self._run_ai_analysis(channel_data, recent_videos)
                channel_data["demographics"] = ai_analysis.get("demographics", {})
                brand_fit = ai_analysis.get("brand_fit", {})
                # priority는 score에서 결정론적으로 파생 (AI 독립 생성 방지)
                brand_fit["priority"] = self._derive_priority(brand_fit.get("score", 0), brand_fit.get("grade", "D"))
                channel_data["brand_fit"] = brand_fit
            else:
                channel_data["demographics"] = {}
                channel_data["brand_fit"] = {}
                if not self.model:
                    channel_data["ai_note"] = "Gemini API 키 미설정으로 AI 분석 생략"

            # 인게이지먼트 지표 계산
            channel_data["engagement"] = self._calculate_engagement(
                channel_data, recent_videos
            )

            # 채널 건강도 계산
            channel_data["channel_health"] = self._calculate_channel_health(
                recent_videos
            )

            # 캐시 저장
            channel_data["analyzed_at"] = datetime.now().isoformat()
            channel_data["from_cache"] = False
            self._save_cache(channel_id, channel_data)

            return channel_data

        except Exception as e:
            return {"error": f"분석 실패: {str(e)}"}

    # ─── URL 파싱 ───

    def _parse_channel_url(self, url_or_id):
        """다양한 YouTube URL 형식에서 채널 ID 추출"""
        url = url_or_id.strip()

        # 이미 채널 ID 형식 (UC로 시작하는 24자)
        if re.match(r"^UC[\w-]{22}$", url):
            return url

        # youtube.com/channel/UCxxxx
        match = re.search(r"youtube\.com/channel/(UC[\w-]{22})", url)
        if match:
            return match.group(1)

        # youtube.com/@handle
        match = re.search(r"youtube\.com/@([\w.-]+)", url)
        if match:
            handle = match.group(1)
            return self._resolve_handle(handle)

        # youtube.com/user/username
        match = re.search(r"youtube\.com/user/([\w.-]+)", url)
        if match:
            username = match.group(1)
            return self._resolve_username(username)

        # youtube.com/c/customname
        match = re.search(r"youtube\.com/c/([\w.-]+)", url)
        if match:
            custom = match.group(1)
            return self._resolve_custom_url(custom)

        # @handle만 입력한 경우
        if url.startswith("@"):
            return self._resolve_handle(url[1:])

        # 채널명으로 검색 시도
        return self._resolve_by_search(url)

    def _resolve_handle(self, handle):
        """@handle로 채널 ID 조회 (1 unit)"""
        try:
            response = (
                self.youtube.channels()
                .list(forHandle=handle, part="id")
                .execute()
            )
            self._track_quota(1)
            items = response.get("items", [])
            return items[0]["id"] if items else None
        except Exception:
            return None

    def _resolve_username(self, username):
        """username으로 채널 ID 조회 (1 unit)"""
        try:
            response = (
                self.youtube.channels()
                .list(forUsername=username, part="id")
                .execute()
            )
            self._track_quota(1)
            items = response.get("items", [])
            return items[0]["id"] if items else None
        except Exception:
            return None

    def _resolve_custom_url(self, custom_name):
        """커스텀 URL로 채널 검색 (100 units, 비효율)"""
        try:
            response = (
                self.youtube.search()
                .list(q=custom_name, type="channel", part="snippet", maxResults=1)
                .execute()
            )
            self._track_quota(100)
            items = response.get("items", [])
            return items[0]["snippet"]["channelId"] if items else None
        except Exception:
            return None

    def _resolve_by_search(self, query):
        """채널명 텍스트로 검색 (100 units)"""
        try:
            response = (
                self.youtube.search()
                .list(q=query, type="channel", part="snippet", maxResults=1)
                .execute()
            )
            self._track_quota(100)
            items = response.get("items", [])
            return items[0]["snippet"]["channelId"] if items else None
        except Exception:
            return None

    # ─── 데이터 파싱 ───

    def _parse_channel_data(self, item):
        """YouTube API 채널 응답을 정제된 딕셔너리로 변환"""
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        branding = item.get("brandingSettings", {}).get("channel", {})

        subscriber_count = int(statistics.get("subscriberCount", 0))
        view_count = int(statistics.get("viewCount", 0))
        video_count = int(statistics.get("videoCount", 0))

        return {
            "channel_id": item["id"],
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "thumbnail": snippet.get("thumbnails", {})
            .get("medium", {})
            .get("url", ""),
            "published_at": snippet.get("publishedAt", ""),
            "country": snippet.get("country", "N/A"),
            "subscriber_count": subscriber_count,
            "subscriber_display": self._format_number(subscriber_count),
            "view_count": view_count,
            "view_display": self._format_number(view_count),
            "video_count": video_count,
            "keywords": branding.get("keywords", ""),
            "custom_url": snippet.get("customUrl", ""),
        }

    def _get_recent_videos(self, uploads_playlist_id):
        """업로드 재생목록에서 최근 영상 가져오기"""
        try:
            # playlistItems.list (1 unit)
            playlist_response = (
                self.youtube.playlistItems()
                .list(
                    playlistId=uploads_playlist_id,
                    part="snippet",
                    maxResults=MAX_RECENT_VIDEOS,
                )
                .execute()
            )
            self._track_quota(1)

            video_ids = [
                item["snippet"]["resourceId"]["videoId"]
                for item in playlist_response.get("items", [])
            ]

            if not video_ids:
                return []

            # videos.list (1 unit) — contentDetails 추가로 duration 수집
            videos_response = (
                self.youtube.videos()
                .list(
                    id=",".join(video_ids),
                    part="snippet,statistics,contentDetails",
                )
                .execute()
            )
            self._track_quota(1)

            videos = []
            for item in videos_response.get("items", []):
                v_snippet = item.get("snippet", {})
                v_stats = item.get("statistics", {})
                view_count = int(v_stats.get("viewCount", 0))
                like_count = int(v_stats.get("likeCount", 0))
                duration_sec = self._parse_duration(
                    item.get("contentDetails", {}).get("duration", "PT0S")
                )

                videos.append(
                    {
                        "video_id": item["id"],
                        "title": v_snippet.get("title", ""),
                        "description": v_snippet.get("description", "")[:200],
                        "published_at": v_snippet.get("publishedAt", ""),
                        "category_id": v_snippet.get("categoryId", ""),
                        "category_name": YOUTUBE_CATEGORIES.get(
                            v_snippet.get("categoryId", ""), "Unknown"
                        ),
                        "tags": v_snippet.get("tags", [])[:10],
                        "view_count": view_count,
                        "view_display": self._format_number(view_count),
                        "like_count": like_count,
                        "like_display": self._format_number(like_count),
                        "duration_seconds": duration_sec,
                        "thumbnail": v_snippet.get("thumbnails", {})
                        .get("medium", {})
                        .get("url", ""),
                    }
                )

            return videos

        except Exception as e:
            print(f"영상 수집 실패: {e}")
            return []

    # ─── 댓글 수집 ───

    def _get_video_comments(self, video_ids, max_per_video=30):
        """인기 영상의 상위 댓글 수집 (행동 맥락 + 인구통계 분석용)

        v3: 5개 영상으로 확대, 작성자 닉네임 추출 추가
        """
        all_comments = []
        # 조회수 높은 상위 5개 영상에서 댓글 수집 (3→5 확대, +2 units)
        for vid in video_ids[:5]:
            try:
                response = (
                    self.youtube.commentThreads()
                    .list(
                        videoId=vid,
                        part="snippet",
                        maxResults=max_per_video,
                        order="relevance",
                        textFormat="plainText",
                    )
                    .execute()
                )
                self._track_quota(1)

                for item in response.get("items", []):
                    c = item["snippet"]["topLevelComment"]["snippet"]
                    text = c["textDisplay"].replace("\n", " ").strip()
                    author = c.get("authorDisplayName", "").strip()
                    # 크리에이터 본인의 고정 댓글(광고 링크) 제외
                    if len(text) > 10 and not text.startswith("http"):
                        all_comments.append(
                            {
                                "text": text[:200],
                                "likes": c.get("likeCount", 0),
                                "author": author,
                            }
                        )
            except Exception:
                continue

        return all_comments

    # ─── AI 분석 ───

    def _run_ai_analysis(self, channel_data, recent_videos):
        """Gemini로 인구통계 추정 + 브랜드 적합도 통합 분석 (v3: 닉네임+벤치마크+어투)"""
        videos_summary = "\n".join(
            [
                f"- [{v['category_name']}] {v['title']} (조회수: {v['view_display']}, 좋아요: {v['like_display']})"
                for v in recent_videos
            ]
        )

        # 댓글 수집 (상위 5개 영상 × 30건, v3 확대)
        video_ids = [v["video_id"] for v in recent_videos]
        comments = self._get_video_comments(video_ids)
        comments_summary = "\n".join(
            [
                f"- [{c['likes']}likes] {c['text']}"
                for c in sorted(comments, key=lambda x: x["likes"], reverse=True)
            ]
        ) if comments else "(댓글 수집 불가)"

        # v3: 댓글 작성자 닉네임 수집 (성별/연령 추론 단서)
        author_names = list(dict.fromkeys(
            c["author"] for c in comments if c.get("author")
        ))
        if author_names:
            commenter_profiles = (
                f"총 {len(author_names)}명 (중복 제거):\n"
                + ", ".join(author_names[:80])
            )
        else:
            commenter_profiles = "(댓글 작성자 정보 없음)"

        # v3: 영상 카테고리 기반 벤치마크
        category_counts = {}
        for v in recent_videos:
            cat = v.get("category_name", "Unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        primary_category = (
            max(category_counts, key=category_counts.get)
            if category_counts else "Unknown"
        )
        benchmark = CATEGORY_BENCHMARKS.get(primary_category, {})
        if benchmark:
            category_benchmark = (
                f"주요 카테고리: {primary_category}\n"
                f"- 업계 평균: {benchmark['typical_demographics']}\n"
                f"- 참고: {benchmark['note']}"
            )
        else:
            category_benchmark = (
                f"주요 카테고리: {primary_category}\n"
                "- 벤치마크 없음. 콘텐츠 기반으로 추정"
            )

        prompt = COMBINED_ANALYSIS_PROMPT.format(
            brand_context=SUU_BRAND_CONTEXT,
            influencer_context=INFLUENCER_CONTEXT,
            channel_name=channel_data["title"],
            channel_description=channel_data["description"][:500],
            subscriber_count=channel_data["subscriber_display"],
            total_views=channel_data["view_display"],
            video_count=channel_data["video_count"],
            published_at=channel_data["published_at"][:10],
            country=channel_data["country"],
            recent_videos_summary=videos_summary,
            comments_summary=comments_summary,
            commenter_profiles=commenter_profiles,
            category_benchmark=category_benchmark,
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=GEMINI_TEMPERATURE,
                    max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
                ),
            )

            text = response.text.strip()
            # JSON 블록 추출
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                return json.loads(json_match.group())
            return {}

        except Exception as e:
            print(f"AI 분석 실패: {e}")
            return {}

    # ─── Priority 자동 파생 ───

    @staticmethod
    def _derive_priority(score, grade):
        """score/grade에서 priority를 결정론적으로 파생 (AI 독립 생성 방지)"""
        if grade in ("S", "A") or score >= 70:
            return "즉시 접촉"
        elif grade == "B" or score >= 55:
            return "검토 필요"
        else:
            return "보류"

    # ─── 인게이지먼트 계산 ───

    def _calculate_engagement(self, channel_data, recent_videos):
        """인게이지먼트 지표 계산"""
        subs = channel_data["subscriber_count"]
        if not subs or not recent_videos:
            return {}

        avg_views = (
            sum(v["view_count"] for v in recent_videos) / len(recent_videos)
            if recent_videos
            else 0
        )
        avg_likes = (
            sum(v["like_count"] for v in recent_videos) / len(recent_videos)
            if recent_videos
            else 0
        )

        view_ratio = (avg_views / subs * 100) if subs > 0 else 0
        like_ratio = (avg_likes / avg_views * 100) if avg_views > 0 else 0

        return {
            "avg_views": int(avg_views),
            "avg_views_display": self._format_number(int(avg_views)),
            "avg_likes": int(avg_likes),
            "avg_likes_display": self._format_number(int(avg_likes)),
            "view_sub_ratio": round(view_ratio, 1),
            "like_view_ratio": round(like_ratio, 1),
        }

    # ─── 캐시 ───

    def _load_cache(self, channel_id):
        """캐시에서 채널 분석 결과 로드 (TTL 초과 시 None)"""
        cache_file = self.cache_dir / f"{channel_id}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            analyzed_at = datetime.fromisoformat(data.get("analyzed_at", ""))
            if datetime.now() - analyzed_at > timedelta(hours=CACHE_TTL_HOURS):
                return None

            return data
        except Exception:
            return None

    def _save_cache(self, channel_id, data):
        """채널 분석 결과를 캐시에 저장"""
        cache_file = self.cache_dir / f"{channel_id}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"캐시 저장 실패: {e}")

    # ─── 유틸리티 ───

    @staticmethod
    def _format_number(num):
        """숫자를 읽기 쉬운 형태로 변환 (1.2만, 345만 등)"""
        if num >= 100_000_000:
            return f"{num / 100_000_000:.1f}억"
        if num >= 10_000:
            return f"{num / 10_000:.1f}만"
        if num >= 1_000:
            return f"{num / 1_000:.1f}천"
        return str(num)

    @staticmethod
    def _parse_duration(iso_duration):
        """ISO 8601 duration (PT1H2M30S) → 초 단위 변환"""
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration or "")
        if not m:
            return 0
        h, mi, s = (int(x) if x else 0 for x in m.groups())
        return h * 3600 + mi * 60 + s

    def _calculate_channel_health(self, recent_videos):
        """채널 건강도 점수 — 업로드 빈도 + 숏폼 비율 + 조회수 추세

        Returns:
            dict: score(0~100), grade(S/A/B/C/D), 세부 지표
        """
        if not recent_videos or len(recent_videos) < 2:
            return {
                "score": 0, "grade": "N/A",
                "upload_frequency": "데이터 부족",
                "days_since_last": None,
                "shorts_ratio": 0,
                "view_trend": "데이터 부족",
                "view_trend_ratio": 0,
            }

        now = datetime.now()

        # ── 1. 업로드 빈도 + 최근 활동일 ──
        dates = []
        for v in recent_videos:
            try:
                dt = datetime.fromisoformat(v["published_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                dates.append(dt)
            except (ValueError, KeyError):
                continue

        dates.sort(reverse=True)
        days_since_last = (now - dates[0]).days if dates else 999

        if len(dates) >= 2:
            span_days = max((dates[0] - dates[-1]).days, 1)
            uploads_per_month = len(dates) / (span_days / 30)
        else:
            uploads_per_month = 0

        # 업로드 빈도 점수 (40점 만점)
        if days_since_last <= 7 and uploads_per_month >= 4:
            freq_score = 40
            freq_label = f"주 {uploads_per_month / 4:.1f}회 (활발)"
        elif days_since_last <= 14 and uploads_per_month >= 2:
            freq_score = 30
            freq_label = f"월 {uploads_per_month:.0f}회 (양호)"
        elif days_since_last <= 30:
            freq_score = 20
            freq_label = f"월 {uploads_per_month:.0f}회 (보통)"
        elif days_since_last <= 90:
            freq_score = 10
            freq_label = f"마지막 업로드 {days_since_last}일 전 (느림)"
        else:
            freq_score = 0
            freq_label = f"마지막 업로드 {days_since_last}일 전 (휴면)"

        # ── 2. 숏폼 비율 ──
        shorts_count = sum(
            1 for v in recent_videos
            if v.get("duration_seconds", 0) <= 60
            or "#shorts" in v.get("title", "").lower()
        )
        shorts_ratio = shorts_count / len(recent_videos)

        # 숏폼 비율 점수 (30점 만점) — 롱폼 비중 높을수록 유리
        if shorts_ratio <= 0.2:
            shorts_score = 30
            shorts_label = f"{shorts_ratio:.0%} (롱폼 중심)"
        elif shorts_ratio <= 0.5:
            shorts_score = 20
            shorts_label = f"{shorts_ratio:.0%} (혼합)"
        elif shorts_ratio <= 0.7:
            shorts_score = 10
            shorts_label = f"{shorts_ratio:.0%} (숏폼 위주)"
        else:
            shorts_score = 0
            shorts_label = f"{shorts_ratio:.0%} (숏폼 전용)"

        # ── 3. 조회수 추세 ──
        mid = len(recent_videos) // 2
        recent_views = [v["view_count"] for v in recent_videos[:mid]]
        older_views = [v["view_count"] for v in recent_videos[mid:]]

        recent_avg = sum(recent_views) / len(recent_views) if recent_views else 0
        older_avg = sum(older_views) / len(older_views) if older_views else 0
        trend_ratio = recent_avg / older_avg if older_avg > 0 else 1.0

        # 추세 점수 (30점 만점)
        if trend_ratio >= 1.2:
            trend_score = 30
            trend_label = f"상승 (+{(trend_ratio - 1) * 100:.0f}%)"
        elif trend_ratio >= 0.8:
            trend_score = 20
            trend_label = "유지"
        elif trend_ratio >= 0.5:
            trend_score = 10
            trend_label = f"하락 ({(trend_ratio - 1) * 100:.0f}%)"
        else:
            trend_score = 0
            trend_label = f"급락 ({(trend_ratio - 1) * 100:.0f}%)"

        # ── 종합 ──
        total = freq_score + shorts_score + trend_score
        if total >= 80:
            grade = "S"
        elif total >= 60:
            grade = "A"
        elif total >= 40:
            grade = "B"
        elif total >= 20:
            grade = "C"
        else:
            grade = "D"

        return {
            "score": total,
            "grade": grade,
            "upload_frequency": freq_label,
            "uploads_per_month": round(uploads_per_month, 1),
            "days_since_last": days_since_last,
            "shorts_ratio": round(shorts_ratio, 2),
            "shorts_label": shorts_label,
            "view_trend": trend_label,
            "view_trend_ratio": round(trend_ratio, 2),
        }

    # ─── 유사 채널 검색 (적합성 필터링) ───

    # 적합성 스코어링에 사용할 키워드 가중치 (행동 맥락 중심)
    _FIT_KEYWORDS = {
        "high": ["가족", "부모", "효도", "선물", "명절", "추석", "설날", "어버이날",
                 "일상", "브이로그", "건강", "한방", "보약", "공진단", "한약",
                 "부부", "아빠", "엄마", "시골부모"],
        "medium": ["웰니스", "육아", "여행", "결혼", "먹방", "리뷰", "추천",
                   "시골", "감동", "집밥", "요리", "중년", "40대", "50대",
                   "피로", "면역", "수면"],
    }

    def search_similar_channels(self, keywords, exclude_channel_id=None, top_n=5):
        """AI 추천 키워드 통합 검색 → 적합성 필터링 → 상위 N개 반환

        Args:
            keywords: 키워드 목록 (최대 3개) 또는 단일 키워드 문자열
            exclude_channel_id: 제외할 채널 ID (현재 분석 중인 채널)
            top_n: 반환할 최대 채널 수
        """
        if not self.youtube:
            return {"error": "YouTube API 키가 설정되지 않았습니다."}

        # 단일 키워드 문자열 → 리스트 변환 (하위 호환)
        if isinstance(keywords, str):
            keywords = [keywords]

        try:
            # 1. 키워드별 검색 → 후보 풀 확보
            seen_ids = set()
            if exclude_channel_id:
                seen_ids.add(exclude_channel_id)

            all_channel_ids = []
            for kw in keywords[:3]:
                search_response = (
                    self.youtube.search()
                    .list(
                        q=kw,
                        type="channel",
                        part="snippet",
                        maxResults=5,
                        order="relevance",
                        regionCode="KR",
                    )
                    .execute()
                )
                self._track_quota(100)

                for item in search_response.get("items", []):
                    cid = item["snippet"]["channelId"]
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        all_channel_ids.append(cid)

            if not all_channel_ids:
                return {"channels": [], "total": 0}

            # 2. 채널 상세 정보 배치 조회
            channels_response = (
                self.youtube.channels()
                .list(
                    id=",".join(all_channel_ids),
                    part="snippet,statistics",
                )
                .execute()
            )
            self._track_quota(1)

            candidates = []
            for item in channels_response.get("items", []):
                ch = self._parse_channel_data(item)
                ch["_fit_score"] = self._score_channel_fit(ch)
                candidates.append(ch)

            # 3. 적합성 필터 + 스코어 정렬 (보통 이상만 — score >= 30)
            filtered = [
                c for c in candidates
                if c["subscriber_count"] >= MIN_SUBSCRIBER_COUNT and c["_fit_score"] >= 30
            ]
            filtered.sort(key=lambda x: x["_fit_score"], reverse=True)

            # 추천 이유 + 힌트 부착 후 반환
            results = []
            for ch in filtered[:top_n]:
                ch["fit_hint"] = self._fit_hint(ch["_fit_score"])
                ch["fit_reason"] = self._get_fit_reason(ch)
                del ch["_fit_score"]
                results.append(ch)

            return {"channels": results, "total": len(results), "pool_size": len(candidates)}

        except Exception as e:
            return {"error": f"유사 채널 검색 실패: {str(e)}"}

    def _score_channel_fit(self, channel_data):
        """채널 설명/키워드 기반 빠른 적합성 점수 (0~100)"""
        score = 0
        text = f"{channel_data.get('description', '')} {channel_data.get('keywords', '')} {channel_data.get('title', '')}".lower()

        # 키워드 매칭
        for kw in self._FIT_KEYWORDS["high"]:
            if kw in text:
                score += 12
        for kw in self._FIT_KEYWORDS["medium"]:
            if kw in text:
                score += 6

        # 구독자 규모 보너스 (1만~100만 구간이 협업 적합)
        subs = channel_data.get("subscriber_count", 0)
        if 10000 <= subs < 100000:
            score += 10  # 마이크로 인플루언서 (비용 효율 우수)
        elif 100000 <= subs < 500000:
            score += 15  # 미드티어
        elif 500000 <= subs < 1000000:
            score += 12
        elif subs >= 1000000:
            score += 8   # 메가 (단가 높음)

        # 한국 채널 보너스
        if channel_data.get("country") == "KR":
            score += 10

        # 점수 상한 100
        return min(score, 100)

    @staticmethod
    def _fit_hint(score):
        """적합성 점수 → 한줄 힌트"""
        if score >= 50:
            return "높은 적합성"
        elif score >= 30:
            return "보통 적합성"
        return "낮은 적합성"

    def _get_fit_reason(self, channel_data):
        """채널이 추천된 이유를 간결한 문자열로 반환"""
        reasons = []
        text = f"{channel_data.get('description', '')} {channel_data.get('keywords', '')} {channel_data.get('title', '')}".lower()

        # 매칭된 키워드 수집
        matched_high = [kw for kw in self._FIT_KEYWORDS["high"] if kw in text]
        matched_med = [kw for kw in self._FIT_KEYWORDS["medium"] if kw in text]
        matched = matched_high + matched_med
        if matched:
            display = matched[:3]  # 최대 3개만 표시
            reasons.append(f"'{', '.join(display)}' 키워드 매칭")

        # 구독자 규모
        subs = channel_data.get("subscriber_count", 0)
        if 10000 <= subs < 100000:
            reasons.append("마이크로 인플루언서")
        elif 100000 <= subs < 500000:
            reasons.append("미드티어 채널")
        elif 500000 <= subs < 1000000:
            reasons.append("대형 채널")
        elif subs >= 1000000:
            reasons.append("메가 채널")

        # 한국 채널
        if channel_data.get("country") == "KR":
            reasons.append("한국 채널")

        return " · ".join(reasons) if reasons else "키워드 기반 추천"

    def export_csv(self, channels_data):
        """채널 목록을 CSV 문자열로 변환"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # 헤더
        writer.writerow(
            [
                "채널명",
                "채널ID",
                "구독자",
                "총 조회수",
                "영상 수",
                "국가",
                "개설일",
                "브랜드 적합도 점수",
                "브랜드 적합도 등급",
                "주요 연령대",
                "성별 비율",
                "우선순위",
                "URL",
            ]
        )

        for ch in channels_data:
            demographics = ch.get("demographics", {})
            brand_fit = ch.get("brand_fit", {})

            age_dist = demographics.get("estimated_age_distribution", {})
            top_age = max(age_dist, key=lambda k: int(age_dist[k].replace("%", "0"))) if age_dist else "N/A"

            gender = demographics.get("estimated_gender_ratio", {})
            gender_str = ", ".join(f"{k}: {v}" for k, v in gender.items()) if gender else "N/A"

            writer.writerow(
                [
                    ch.get("title", ""),
                    ch.get("channel_id", ""),
                    ch.get("subscriber_count", 0),
                    ch.get("view_count", 0),
                    ch.get("video_count", 0),
                    ch.get("country", "N/A"),
                    ch.get("published_at", "")[:10],
                    brand_fit.get("score", "N/A"),
                    brand_fit.get("grade", "N/A"),
                    top_age,
                    gender_str,
                    brand_fit.get("priority", "N/A"),
                    f"https://youtube.com/channel/{ch.get('channel_id', '')}",
                ]
            )

        return output.getvalue()
