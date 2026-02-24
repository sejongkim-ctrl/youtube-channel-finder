/**
 * YouTube Channel Finder - Frontend Logic
 */

// 상태 관리
let searchResultsData = [];
let analyzedChannelsData = [];
let currentAnalysisData = null;  // 현재 분석 중인 채널 데이터

// ─── 탭 전환 ───

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName === 'search' ? 'searchPanel' : 'analyzePanel').classList.add('active');
}

// ─── 검색 ───

function searchPreset(keyword) {
    document.getElementById('searchKeyword').value = keyword;
    searchChannels();
}

async function searchChannels() {
    const keyword = document.getElementById('searchKeyword').value.trim();
    if (!keyword) return;

    showLoading('채널 검색 중...');
    hideError();
    hideResults();

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword, max_results: 10 })
        });
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        searchResultsData = data.channels || [];
        renderSearchResults(searchResultsData);
    } catch (err) {
        showError('서버 연결에 실패했습니다. Flask 서버가 실행 중인지 확인하세요.');
    } finally {
        hideLoading();
    }
}

// ─── 채널 분석 ───

async function analyzeChannel(channelInput) {
    const input = channelInput || document.getElementById('channelUrl')?.value?.trim();
    if (!input) return;

    showLoading('채널 분석 중... (AI 분석에 10~20초 소요)');
    hideError();

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel_input: input })
        });
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        // 분석된 채널 데이터 저장
        const existingIdx = analyzedChannelsData.findIndex(c => c.channel_id === data.channel_id);
        if (existingIdx >= 0) {
            analyzedChannelsData[existingIdx] = data;
        } else {
            analyzedChannelsData.push(data);
        }

        renderAnalysis(data);
        updateQuota();
    } catch (err) {
        showError('분석 요청에 실패했습니다.');
    } finally {
        hideLoading();
    }
}

async function analyzeFromCard(channelId) {
    // 카드의 버튼 비활성화
    const btn = document.querySelector(`[data-channel-id="${channelId}"]`);
    if (btn) {
        btn.disabled = true;
        btn.textContent = '분석 중...';
    }

    await analyzeChannel(channelId);

    if (btn) {
        btn.disabled = false;
        btn.textContent = '상세 분석';
    }
}

// ─── 렌더링: 검색 결과 ───

function renderSearchResults(channels) {
    const container = document.getElementById('channelCards');
    document.getElementById('resultCount').textContent = channels.length;

    container.innerHTML = channels.map(ch => `
        <div class="channel-card">
            <img src="${ch.thumbnail}" alt="${ch.title}" class="channel-avatar"
                 onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 56 56%22><rect fill=%22%231a2332%22 width=%2256%22 height=%2256%22/><text x=%2228%22 y=%2234%22 text-anchor=%22middle%22 fill=%22%238b98a5%22 font-size=%2220%22>?</text></svg>'">
            <div class="channel-info">
                <div class="channel-name">${escapeHtml(ch.title)}</div>
                <div class="channel-desc">${escapeHtml(ch.description?.substring(0, 120) || '')}</div>
                <div class="channel-stats">
                    <span>구독자 ${ch.subscriber_display}</span>
                    <span>영상 ${ch.video_count.toLocaleString()}개</span>
                    <span>조회수 ${ch.view_display}</span>
                    <span>${ch.country}</span>
                </div>
            </div>
            <button class="analyze-btn" data-channel-id="${ch.channel_id}"
                    onclick="analyzeFromCard('${ch.channel_id}')">
                상세 분석
            </button>
        </div>
    `).join('');

    document.getElementById('searchResults').classList.remove('hidden');
    document.getElementById('exportBtn').disabled = false;
    updateQuota();
}

// ─── 렌더링: 상세 분석 ───

function renderAnalysis(data) {
    currentAnalysisData = data;  // 현재 채널 저장
    const section = document.getElementById('analysisResult');
    section.classList.remove('hidden');

    // 유사 채널 섹션 초기화
    const similarSection = document.getElementById('similarChannelsSection');
    if (similarSection) {
        similarSection.classList.add('hidden');
        similarSection.innerHTML = '';
    }

    // 기본 정보
    document.getElementById('analysisTitle').textContent = data.title;
    document.getElementById('analysisThumbnail').src = data.thumbnail;
    document.getElementById('aSubs').textContent = data.subscriber_display;
    document.getElementById('aViews').textContent = data.view_display;
    document.getElementById('aVideos').textContent = `${data.video_count.toLocaleString()}개`;
    document.getElementById('aDate').textContent = data.published_at?.substring(0, 10) || 'N/A';
    document.getElementById('aCountry').textContent = data.country;

    // 캐시 표시
    const cacheBadge = document.getElementById('cacheIndicator');
    if (data.from_cache) {
        cacheBadge.classList.remove('hidden');
    } else {
        cacheBadge.classList.add('hidden');
    }

    // 인게이지먼트
    const engEl = document.getElementById('engagementStats');
    const eng = data.engagement || {};
    if (eng.avg_views) {
        engEl.innerHTML = `
            <div class="engagement-row"><span>평균 조회수</span><span>${eng.avg_views_display}</span></div>
            <div class="engagement-row"><span>평균 좋아요</span><span>${eng.avg_likes_display}</span></div>
            <div class="engagement-row"><span>조회/구독 비율</span><span>${eng.view_sub_ratio}%</span></div>
            <div class="engagement-row"><span>좋아요/조회 비율</span><span>${eng.like_view_ratio}%</span></div>
        `;
    } else {
        engEl.innerHTML = '';
    }

    // 인구통계
    renderDemographics(data.demographics || {});

    // 브랜드 적합도
    renderBrandFit(data.brand_fit || {});

    // 최근 영상
    renderRecentVideos(data.recent_videos || []);

    // 스크롤
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderDemographics(demo) {
    const container = document.getElementById('demographicsContent');

    if (!demo || !demo.estimated_age_distribution) {
        container.innerHTML = '<p class="no-data">AI 분석 데이터 없음 (Gemini API 키 확인)</p>';
        return;
    }

    const ageDist = demo.estimated_age_distribution || {};
    const genderRatio = demo.estimated_gender_ratio || {};
    const interests = demo.primary_interests || [];
    const persona = demo.audience_persona || '';
    const confidence = demo.confidence_level || 'low';

    // 연령 분포 바 차트
    let ageHtml = '<div class="demo-section"><div class="demo-section-title">연령 분포 (추정)</div>';
    for (const [age, pct] of Object.entries(ageDist)) {
        const numPct = parseInt(pct) || 0;
        ageHtml += `
            <div class="age-bar">
                <span class="age-label">${age}</span>
                <div class="age-bar-fill" style="width: ${numPct * 2}px"></div>
                <span class="age-percent">${pct}</span>
            </div>
        `;
    }
    ageHtml += '</div>';

    // 성별 비율
    let genderHtml = '<div class="demo-section"><div class="demo-section-title">성별 비율 (추정)</div>';
    for (const [gender, pct] of Object.entries(genderRatio)) {
        const numPct = parseInt(pct) || 0;
        const color = gender === '남성' ? 'var(--blue)' : 'var(--red)';
        genderHtml += `
            <div class="age-bar">
                <span class="age-label">${gender}</span>
                <div class="age-bar-fill" style="width: ${numPct * 2}px; background: ${color}"></div>
                <span class="age-percent">${pct}</span>
            </div>
        `;
    }
    genderHtml += '</div>';

    // 관심사 태그
    let interestHtml = '<div class="demo-section"><div class="demo-section-title">주요 관심사</div><div class="interest-tags">';
    interestHtml += interests.map(i => `<span class="interest-tag">${escapeHtml(i)}</span>`).join('');
    interestHtml += '</div></div>';

    // 페르소나
    let personaHtml = persona
        ? `<div class="demo-section"><div class="demo-section-title">시청자 페르소나</div><p class="persona-text">${escapeHtml(persona)}</p></div>`
        : '';

    // 신뢰도
    const confClass = confidence === 'high' ? 'confidence-high' : confidence === 'medium' ? 'confidence-medium' : 'confidence-low';
    const confLabel = confidence === 'high' ? '높음' : confidence === 'medium' ? '보통' : '낮음';

    container.innerHTML = ageHtml + genderHtml + interestHtml + personaHtml +
        `<span class="confidence-badge ${confClass}">추정 신뢰도: ${confLabel}</span>`;
}

function renderBrandFit(fit) {
    const container = document.getElementById('brandFitContent');

    if (!fit || fit.score === undefined) {
        container.innerHTML = '<p class="no-data">AI 분석 데이터 없음 (Gemini API 키 확인)</p>';
        return;
    }

    const grade = fit.grade || 'D';
    const score = fit.score || 0;
    const priority = fit.priority || '보류';

    const gradeClass = `grade-${grade}`;

    let priorityClass = 'priority-hold';
    if (priority.includes('즉시')) priorityClass = 'priority-urgent';
    else if (priority.includes('검토')) priorityClass = 'priority-review';

    const topicScore = fit.topic_fit_score || '-';
    const behavioralScore = fit.behavioral_fit_score || '-';
    const capabilityScore = fit.channel_capability_score || '-';
    const bestTiming = fit.best_timing || '';

    // verdict 섹션 (최상단)
    const verdictHtml = fit.verdict
        ? `<div class="verdict-box ${gradeClass}">${escapeHtml(fit.verdict)}</div>`
        : '';

    let html = `
        <div class="brand-fit-header">
            <span class="fit-score ${gradeClass}">${score}</span>
            <span class="fit-grade ${gradeClass}">${grade}</span>
            <span class="fit-priority ${priorityClass}">${escapeHtml(priority)}</span>
        </div>
        ${verdictHtml}
        <div class="fit-scores-dual">
            <div class="fit-score-axis">
                <span class="axis-label">주제 적합</span>
                <span class="axis-value">${topicScore}<small>/25</small></span>
            </div>
            <div class="fit-score-axis">
                <span class="axis-label">행동 맥락</span>
                <span class="axis-value">${behavioralScore}<small>/45</small></span>
            </div>
            <div class="fit-score-axis">
                <span class="axis-label">채널 역량</span>
                <span class="axis-value">${capabilityScore}<small>/30</small></span>
            </div>
        </div>
        ${bestTiming ? `<div class="fit-timing">최적 협업 시기: <strong>${escapeHtml(bestTiming)}</strong></div>` : ''}
        <div class="fit-sr-grid">
            <div>
                <h4>강점</h4>
                ${renderStrengthCategories(fit.strengths)}
            </div>
            <div>
                <h4>리스크</h4>
                ${renderRiskCategories(fit.risks)}
            </div>
        </div>
        <div class="fit-extras">
            <div>
                <h4>협업 아이디어</h4>
                <ul class="fit-list ideas">
                    ${(fit.collaboration_ideas || []).map(i => `<li>${escapeHtml(i)}</li>`).join('')}
                </ul>
            </div>
            <div>
                <p class="fit-cpm">예상 CPM: ${escapeHtml(fit.estimated_cpm || 'N/A')}</p>
            </div>
        </div>
    `;

    if (fit.reasoning) {
        html += `<div class="fit-reasoning">${escapeHtml(fit.reasoning)}</div>`;
    }

    if (fit.similar_channel_keywords && fit.similar_channel_keywords.length > 0) {
        const keywordsJson = JSON.stringify(fit.similar_channel_keywords).replace(/'/g, "\\'");
        html += `
            <div class="similar-keywords">
                <button class="similar-search-btn" onclick='findSimilarChannels(${keywordsJson})'>
                    유사 채널 탐색
                </button>
                <span class="similar-hint">${fit.similar_channel_keywords.map(k => escapeHtml(k)).join(' · ')}</span>
            </div>
        `;
    }

    container.innerHTML = html;
}

// ─── 강점/리스크 카테고리 렌더링 ───

const STRENGTH_LABELS = {
    gift_motivation: { label: '선물 구매 동기', icon: '🎁' },
    trust_transfer: { label: '신뢰 전이력', icon: '🤝' },
    premium_fit: { label: '프리미엄 적합', icon: '💎' },
    content_synergy: { label: '콘텐츠 시너지', icon: '🎯' },
    seasonal_fit: { label: '시즌 활용도', icon: '📅' },
};

const RISK_LABELS = {
    audience_mismatch: { label: '시청자 불일치', icon: '👥' },
    content_conflict: { label: '콘텐츠 충돌', icon: '⚡' },
    premium_gap: { label: '프리미엄 괴리', icon: '💰' },
    trust_risk: { label: '신뢰도 리스크', icon: '🔒' },
    competitor_exposure: { label: '경쟁 노출', icon: '🔍' },
};

function renderStrengthCategories(strengths) {
    if (!strengths) return '<p class="no-data">강점 데이터 없음</p>';

    // 이전 배열 포맷 하위 호환
    if (Array.isArray(strengths)) {
        return `<ul class="fit-list strengths">${strengths.map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul>`;
    }

    let html = '<div class="strength-categories">';
    for (const [key, value] of Object.entries(strengths)) {
        if (!value || value === '해당 없음') continue;
        const meta = STRENGTH_LABELS[key] || { label: key, icon: '+' };
        html += `
            <div class="strength-item">
                <div class="strength-header">
                    <span class="strength-icon">${meta.icon}</span>
                    <span class="strength-label">${meta.label}</span>
                </div>
                <p class="strength-detail">${escapeHtml(value)}</p>
            </div>
        `;
    }
    html += '</div>';
    return html;
}

function renderRiskCategories(risks) {
    if (!risks) return '<p class="no-data">리스크 데이터 없음</p>';

    // 이전 배열 포맷 하위 호환
    if (Array.isArray(risks)) {
        return `<ul class="fit-list risks">${risks.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>`;
    }

    let html = '<div class="risk-categories">';
    for (const [key, value] of Object.entries(risks)) {
        if (!value || value === '해당 없음') continue;
        const meta = RISK_LABELS[key] || { label: key, icon: '!' };
        html += `
            <div class="risk-item">
                <div class="risk-header">
                    <span class="risk-icon">${meta.icon}</span>
                    <span class="risk-label">${meta.label}</span>
                </div>
                <p class="risk-detail">${escapeHtml(value)}</p>
            </div>
        `;
    }
    html += '</div>';
    return html;
}

// ─── 유사 채널 통합 탐색 ───

async function findSimilarChannels(keywords) {
    const container = document.getElementById('similarChannelsSection');
    if (!container) return;

    const excludeId = currentAnalysisData?.channel_id || null;

    container.classList.remove('hidden');
    container.innerHTML = `
        <h3>유사 채널 추천</h3>
        <div class="loading-inline">
            <div class="spinner-sm"></div>
            <span>적합 채널 탐색 중... (${keywords.length}개 키워드 통합 검색)</span>
        </div>
    `;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });

    try {
        const response = await fetch('/api/similar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords, exclude_channel_id: excludeId, top_n: 5 })
        });
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<h3>유사 채널 추천</h3><p class="no-data">${escapeHtml(data.error)}</p>`;
            return;
        }

        renderSimilarChannels(data.channels || [], data.pool_size || 0);
        updateQuota();
    } catch (err) {
        container.innerHTML = `<h3>유사 채널 추천</h3><p class="no-data">유사 채널 검색 실패</p>`;
    }
}

function renderSimilarChannels(channels, poolSize) {
    const container = document.getElementById('similarChannelsSection');
    if (!container) return;

    if (channels.length === 0) {
        container.innerHTML = `<h3>유사 채널 추천</h3><p class="no-data">적합한 유사 채널을 찾지 못했습니다 (${poolSize}개 후보 중 필터 통과 0개)</p>`;
        return;
    }

    let html = `<h3>유사 채널 추천 <small>${poolSize}개 후보 중 상위 ${channels.length}개</small></h3>`;
    html += '<div class="similar-cards">';

    channels.forEach(ch => {
        const fitClass = ch.fit_hint === '높은 적합성' ? 'fit-high' : ch.fit_hint === '보통 적합성' ? 'fit-medium' : 'fit-low';
        html += `
            <div class="similar-card">
                <img src="${ch.thumbnail}" alt="${escapeHtml(ch.title)}" class="similar-avatar"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 40 40%22><rect fill=%22%231a2332%22 width=%2240%22 height=%2240%22/><text x=%2220%22 y=%2226%22 text-anchor=%22middle%22 fill=%22%238b98a5%22 font-size=%2214%22>?</text></svg>'">
                <div class="similar-info">
                    <div class="similar-name">${escapeHtml(ch.title)}</div>
                    <div class="similar-stats">
                        <span>${ch.subscriber_display} 구독</span>
                        <span>${ch.video_count.toLocaleString()}개 영상</span>
                        <span class="fit-badge ${fitClass}">${escapeHtml(ch.fit_hint || '')}</span>
                    </div>
                </div>
                <button class="analyze-btn-sm" data-channel-id="${ch.channel_id}"
                        onclick="analyzeFromSimilar('${ch.channel_id}', this)">
                    분석
                </button>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

async function analyzeFromSimilar(channelId, btn) {
    if (btn) {
        btn.disabled = true;
        btn.textContent = '분석 중...';
    }
    await analyzeChannel(channelId);
    if (btn) {
        btn.disabled = false;
        btn.textContent = '분석';
    }
}

function renderRecentVideos(videos) {
    const container = document.getElementById('recentVideos');

    if (!videos || videos.length === 0) {
        container.innerHTML = '<p class="no-data">영상 데이터 없음</p>';
        return;
    }

    let html = `
        <table class="video-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>제목</th>
                    <th>카테고리</th>
                    <th style="text-align:right">조회수</th>
                    <th style="text-align:right">좋아요</th>
                </tr>
            </thead>
            <tbody>
    `;

    videos.forEach((v, i) => {
        html += `
            <tr>
                <td style="color:var(--text-dim)">${i + 1}</td>
                <td class="video-title">
                    <a href="https://youtube.com/watch?v=${v.video_id}" target="_blank" rel="noopener">
                        ${escapeHtml(v.title)}
                    </a>
                </td>
                <td style="color:var(--text-muted);font-size:12px">${escapeHtml(v.category_name)}</td>
                <td class="video-stat">${v.view_display}</td>
                <td class="video-stat">${v.like_display}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ─── CSV 내보내기 ───

async function exportCsv() {
    // 분석된 채널이 있으면 분석 데이터 포함, 없으면 검색 결과만
    const dataToExport = analyzedChannelsData.length > 0 ? analyzedChannelsData : searchResultsData;

    if (dataToExport.length === 0) {
        showError('내보낼 데이터가 없습니다.');
        return;
    }

    try {
        const response = await fetch('/api/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channels: dataToExport })
        });

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `youtube_channels_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        showError('CSV 내보내기에 실패했습니다.');
    }
}

// ─── Quota 업데이트 ───

async function updateQuota() {
    try {
        const response = await fetch('/api/quota');
        const data = await response.json();
        document.getElementById('quotaCount').textContent = data.quota_used;
    } catch (err) {
        // 무시
    }
}

// ─── UI 헬퍼 ───

function showLoading(text) {
    document.getElementById('loadingText').textContent = text || '처리 중...';
    document.getElementById('loading').classList.remove('hidden');
}
function hideLoading() { document.getElementById('loading').classList.add('hidden'); }

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = msg;
    el.classList.remove('hidden');
}
function hideError() { document.getElementById('errorMsg').classList.add('hidden'); }

function hideResults() {
    document.getElementById('searchResults').classList.add('hidden');
}

function closeAnalysis() {
    document.getElementById('analysisResult').classList.add('hidden');
}

function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}
