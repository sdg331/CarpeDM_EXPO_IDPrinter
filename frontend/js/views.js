import { teams, modes } from "./content.js";
import { icon, logo } from "./icons.js";
import { errorCopy } from "./api-client.js";

export const escape = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
const btn = (action, text, style = "", symbol = "arrow", disabled = false, loading = false) =>
  `<button class="button ${style}" data-action="${action}" ${disabled ? "disabled" : ""}${loading ? ' aria-busy="true"' : ""}>${text}${loading ? '<span class="spinner-inline" aria-hidden="true"></span>' : symbol ? icon(symbol) : ""}</button>`;
const actions = (content) => `<div class="actions">${content}</div>`;
const heading = (eyebrow, title, subtitle = "") =>
  `<div class="title-group"><div class="eyebrow">${eyebrow}</div><h1>${title}</h1>${subtitle ? `<p class="subtitle">${subtitle}</p>` : ""}</div>`;
const step = (index, text, back = true, total = 5) =>
  `<div class="step-row">${back ? `<button class="back" data-action="back" aria-label="이전 단계">${icon("back")}</button>` : ""}<span class="step-context"><b>${String(index).padStart(2, "0")}</b> / ${text}</span><span class="progress-rail" aria-label="전체 ${total}단계 중 ${index}단계">${Array.from({ length: total }, (_, i) => `<i class="${i < index ? "done" : ""}"></i>`).join("")}</span></div>`;
const teamIcon = (team) =>
  `<span class="team-icon team-image team-${team.id}" aria-hidden="true"><img src="${escape(team.iconImage)}" alt="" width="1254" height="1254" decoding="async"></span>`;

export function renderTeamPreview(team) {
  if (!team) return "";
  return `<div class="overlay-backdrop"><section class="dialog team-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="team-preview-title" aria-describedby="team-preview-description">
    <button class="team-preview-close" data-action="modal-close" aria-label="팀 설명 닫기">${icon("close")}</button>
    <div class="team-preview-hero"><div class="team-preview-image">${teamIcon(team)}</div><div><p class="section-label">MIRRORTING WORKS · ${escape(team.english)}</p><h2 id="team-preview-title">${escape(team.title)}</h2><p id="team-preview-description">${escape(team.description)}</p></div></div>
    <div class="team-preview-content"><section aria-labelledby="team-preview-work"><p class="team-preview-label" id="team-preview-work">주요 업무</p><ol class="team-preview-tasks">${team.tasks.map((task, index) => `<li><span>${String(index + 1).padStart(2, "0")}</span>${escape(task)}</li>`).join("")}</ol></section><section aria-labelledby="team-preview-keyword"><p class="team-preview-label" id="team-preview-keyword">TEAM KEYWORDS</p><div class="team-preview-keywords">${team.keywords.map((keyword) => `<span># ${escape(keyword)}</span>`).join("")}</div></section></div>
    <div class="dialog-actions team-preview-actions">${btn("team-confirm", `${escape(team.title)}으로 입사하기`)}${btn("modal-close", "다른 팀 둘러보기", "secondary", "")}</div>
  </section></div>`;
}
const helper = (text, symbol = "shield") =>
  `<p class="helper">${icon(symbol)}${text}</p>`;
const modeArt = (mode) =>
  `<div class="mode-art" aria-hidden="true"><img class="mode-cover" src="/static/assets/ai-mode-${mode.toLowerCase()}-cover.jpg" alt="" width="720" height="720" decoding="async"></div>`;
const identity = (s) =>
  `<div class="identity-strip">${s.result?.image ? `<img src="${escape(s.result.image)}" alt="현재 프로필">` : icon("badge")}<div><strong>${escape(s.name)}</strong><p>${escape(s.team?.title)} · ${s.aiMode ? escape(modes[s.aiMode].title) : "MIRRORTING WORKS"}</p></div><span class="pill">${escape(s.sessionId || "입사 등록 중")}</span></div>`;
const statusVisual = (symbol, working = false, nfc = false) =>
  `<div class="status-visual ${working ? "working" : ""}">${nfc ? `<div class="nfc-art">${logo()}<span>사원증</span></div>${icon("nfc", "tap-waves")}` : icon(symbol)}</div>`;
const faceMap = (mode = "B", camera = false, showStages = false) => {
  const pipeline = mode === "A"
    ? ["YuNet 얼굴 감지", "SFace 128D 특징", "8개 캐릭터 비교"]
    : ["YuNet 랜드마크", "로컬 인물 분리", "프로필 구도 생성"];
  return `<div class="ai-facemap ${camera ? "camera-facemap" : ""}" aria-hidden="true">
    <div class="facemap-viewport"><span class="facemap-corner corner-tl"></span><span class="facemap-corner corner-tr"></span><span class="facemap-corner corner-bl"></span><span class="facemap-corner corner-br"></span>
      <svg class="facemap-svg" viewBox="0 0 320 360" focusable="false">
        <g class="facemap-mesh"><path class="facemap-outline" d="M160 35c-64 0-105 48-105 119 0 58 25 136 105 171 80-35 105-113 105-171 0-71-41-119-105-119Z"/><path d="M87 137c22-14 48-18 73-18s51 4 73 18M82 181c27 15 51 20 78 20s51-5 78-20M109 239c33 13 69 13 102 0M160 35v290M55 154l105 47 105-47M76 219l84-18 84 18M93 93l67 26 67-26"/><path d="M112 151c13-8 26-8 39 0M169 151c13-8 26-8 39 0M139 242c14 8 28 8 42 0"/></g>
        <g class="facemap-nodes">${[[160,35],[93,93],[227,93],[55,154],[112,151],[151,151],[169,151],[208,151],[160,201],[76,219],[244,219],[139,242],[181,242],[160,325]].map(([x,y], index) => `<circle cx="${x}" cy="${y}" r="4" style="--node-delay:${index * 90}ms"></circle>`).join("")}</g>
      </svg><span class="facemap-axis axis-x"></span><span class="facemap-axis axis-y"></span><span class="facemap-scan"></span>
      <span class="facemap-badge">FACE MAP · LOCAL AI</span>
    </div>
    ${camera || !showStages ? "" : `<ol class="analysis-pipeline">${pipeline.map((label, index) => `<li><span>0${index + 1}</span>${label}</li>`).join("")}</ol>`}
  </div>`;
};
const errorPanel = (error) => {
  if (!error) return "";
  const [title, copy] = errorCopy[error.code] || errorCopy.BACKEND_UNAVAILABLE;
  return `<div class="error-box" role="alert"><h3>${title}</h3><p>${copy}</p></div>`;
};
const errorActions = (s, retry) =>
  s.error?.code === "UNKNOWN_OUTCOME"
    ? btn("operation-check", s.reconciling ? "작업 상태 확인 중" : "작업 상태 다시 확인", "secondary", "info", s.reconciling, s.reconciling) + helper("결과가 불확실합니다. 현장 스태프가 실물을 확인할 때까지 재출력을 요청하지 마세요.", "info")
    : s.error?.code === "PROFILE_EXPIRED"
      ? btn("profile-retake", "프로필 다시 촬영하기", "", "camera")
    : `${s.error?.retryable ? btn(retry, "다시 시도하기", "", "arrow") : ""}${btn("home", "처음으로", "secondary", "")}`;

function home(demo, web) { return webHome(demo, web); }

function webHome(demo = false, web = false) {
  return `<div class="kiosk-welcome"><div class="welcome-copy"><p class="kiosk-kicker">MIRRORTING WORKS · 2026 EXPO</p><h1>입사하신 것을<br>진심으로 축하드립니다.</h1><p class="subtitle">오늘의 직장 생활을 시작해볼까요?</p><p class="pi-intro">${demo ? "샘플 체험에서는 준비된 데이터로 화면만 진행해요." : web ? "웹 미리보기에서는 카메라와 로컬 AI를 사용하고, 카드·실물 출력은 건너뛰어요." : "AI 프로필을 만든 뒤 카드를 등록하고 사원증 출력 작업을 진행해요."}</p></div>
  <div class="welcome-card-area"><div class="pi-kiosk-frame"><div class="pi-runtime"><span><i></i> EXPO KIOSK</span><small>4-FIT MIRRORTING</small></div><div class="welcome-id"><div class="welcome-id-brand">${logo()}<span>MIRRORTING WORKS</span></div><div class="welcome-id-photo"><img src="/assets/characters/char_01.png" alt="사원증 디자인 예시"></div><strong>김미래</strong><span>디자인팀</span><small>사원증 디자인 예시 · 실제 방문객 정보 아님</small></div><ul class="pi-device-strip" aria-label="키오스크 체험 단계"><li>${icon("camera")}<span>카메라</span></li><li>${icon("spark")}<span>로컬 AI</span></li><li>${icon("nfc")}<span>NFC</span></li><li>${icon("printer")}<span>출력</span></li></ul></div></div></div>
  <div class="kiosk-entry-actions"><button class="kiosk-entry checkin-entry" data-action="checkin"><span class="entry-symbol">${icon("badge")}</span><span><strong>출근하기</strong><small>AI 프로필로 사원증 만들기</small></span>${icon("arrow")}</button><button class="kiosk-entry checkout-entry" data-action="checkout"><span class="entry-symbol">${icon("logout")}</span><span><strong>퇴근하기</strong><small>오늘의 체험 리포트 확인</small></span>${icon("arrow")}</button></div>
  <ol class="kiosk-journey" aria-label="전시 체험 순서"><li><span>01</span><div><strong>입사 · 사원증</strong><small>지금 이 키오스크에서</small></div></li><li><span>02</span><div><strong>MirrorTing 체험</strong><small>스마트미러에서</small></div></li><li><span>03</span><div><strong>퇴근 · 리포트</strong><small>다시 키오스크에서</small></div></li></ol>`;
}

function webCamera(s) {
  return `${step(3, "사진 준비")}${heading("", "내 얼굴을 담아볼까요?", "밝은 곳에서 얼굴 전체가 보이도록 정면을 바라봐주세요.")}
  <div class="camera-panel" id="camera-panel"><video id="camera-video" autoplay muted playsinline aria-label="카메라 프리뷰"></video>${faceMap(s.aiMode, true)}<span class="camera-caption">카메라 촬영 · AI 얼굴 감지</span><p class="camera-instruction" id="camera-instruction" role="status">카메라 권한과 연결을 확인하고 있어요.</p></div>
  <p class="camera-state-note">사진은 로컬 AI 서버에서 처리해요. 현장에서는 같은 처리가 Raspberry Pi 안에서 실행되며, 원본은 디스크에 저장하지 않아요.</p><div id="camera-error"></div>
  ${actions(btn("capture", "이 모습으로 촬영하기", "", "camera", true) + btn("camera-retry", "카메라 다시 연결하기", "", "").replace('data-action="camera-retry"', 'data-action="camera-retry" hidden'))}`;
}

function webResult(s) {
  return `${step(3, "AI 프로필 확인")}${heading("", s.aiMode === "A" ? "나와 닮은 캐릭터예요." : "내 프로필이 완성됐어요.", "이 프로필로 나만의 사원증을 만들 수 있어요.")}
  <div class="result-pass"><div class="pass-header">MIRRORTING WORKS ${logo()}</div><div class="pass-photo"><img src="${escape(s.result.image)}" alt="이번 사진으로 처리한 AI 프로필 결과"></div><div class="pass-info"><div><h2>${escape(s.name)}</h2><p>${escape(s.team.title)}</p></div></div><div class="pass-number">2026 EXPO · 입사 프로필</div></div>
  <p class="result-explanation">${s.aiMode === "A" ? "8명의 캐릭터와 얼굴 특징을 비교한 결과예요." : "얼굴과 옷은 그대로, 얼굴이 잘 보이도록 구도를 잡았어요. 머리카락 경계는 촬영 상태에 따라 달라질 수 있어요."}</p>
  ${errorPanel(s.error)}${actions(btn("card-connect", "이 프로필로 입사하기", "", "badge", s.busy) + btn("retake", "다시 촬영하기", "text", "", s.busy))}`;
}

function webIssue(s) {
  return `${step(4, "사원증 카드 연결")}${heading("", "사원증을 리더에<br>올려주세요.", "현장에서는 화면 아래의 카드 리더로 사원증을 등록해요.")}
  <div class="device-step"><div class="reader-visual">${icon("badge")}${icon("nfc")}</div><div><span class="device-pending">웹 시연 · ACR1252U 미연결</span><h2>Raspberry Pi 카드 등록 단계예요.</h2><p>현장 키오스크에서는 Pi에 연결된 NFC 리더로 카드를 확인해요.<br>웹에서는 실제 쓰기 대신 출력 화면을 먼저 확인할 수 있어요.</p></div></div>
  <div class="issue-person"><img src="${escape(s.result.image)}" alt="연결할 입사 프로필"><div><strong>${escape(s.name)}</strong><span>${escape(s.team.title)}</span></div></div>
  ${errorPanel(s.error)}${actions(btn("digital-card", s.busy ? "출력 이미지 준비 중" : "출력 화면 미리보기", "", "printer", s.busy, s.busy) + btn("retake", "사진 다시 촬영하기", "text", "", s.busy))}`;
}

function webCard(s) {
  return `${step(5, "사원증 출력", false)}${heading("", "이 모습으로<br>사원증이 나와요.", "인쇄 전에 이름과 프로필을 확인해주세요.")}
  <div class="print-preview"><img class="digital-card-preview" src="${escape(s.digitalCard)}" alt="${escape(s.name)}님의 저장 가능한 사원증"><div class="print-description"><span class="device-pending">웹 시연 · ZTP-80USL2 미연결</span><h2>Raspberry Pi에서 출력될 사원증이에요.</h2><p>현장에서는 Pi가 감열 프린터에 출력 작업을 보내고,<br>발급된 사원증으로 MirrorTing 체험을 이어가요.</p><p class="hardware-note">현재 웹에서는 실물 카드 등록이나 출력을 진행하지 않았어요.</p></div></div>
  ${actions(btn("visit-guide", "다음 체험 안내", "", "arrow") + `<a class="button text" href="${escape(s.digitalCard)}" download="MIRRORTING-ID.png">사원증 PNG 저장</a>`)} `;
}

function webComplete() {
  return `${heading("", "다음은,<br>MirrorTing에서 만나요.", "스마트미러 체험을 마친 뒤 이 키오스크에서 퇴근해주세요.")}
  <div class="mirror-next">${icon("mirror")}<div><span class="kiosk-kicker">02 · 스마트미러 체험</span><h2>나를 비추는 새로운 경험</h2><p>사원증 확인 → MirrorTing 체험 → 퇴근 리포트</p></div></div>
  <div class="kiosk-notice"><strong>오늘의 브라우저 시연은 여기까지예요.</strong><p>프로필과 출력 이미지는 실제로 만들었어요. 카드 등록·실물 출력·스마트미러 연결은 현장 장치가 필요해요.</p></div>
  ${actions(btn("home", "처음 화면으로", "", "arrow"))}`;
}

function webCheckout() {
  return `${step(1, "퇴근 · 사원증 확인", true, 2)}${heading("", "오늘의 체험을<br>돌아볼까요?", "사원증을 확인하면 MirrorTing 체험 리포트로 이어져요.")}
  <div class="device-step"><div class="reader-visual">${icon("badge")}${icon("nfc")}</div><div><span class="device-pending">카드 리더 미연결</span><h2>사원증 확인이 필요해요.</h2><p>지금은 스마트미러 체험 기록도 연결되지 않았어요.<br>퇴근 리포트가 표시될 화면을 미리 볼 수 있어요.</p></div></div>
  ${actions(btn("report-preview", "퇴근 리포트 화면 보기", "", "receipt") + btn("home", "처음 화면으로", "text", ""))}`;
}

function webReport() {
  return `${step(2, "퇴근 · 리포트 확인", true, 2)}${heading("", "오늘의 기록이<br>리포트로 모여요.", "사원증과 스마트미러를 연결하면 체험 기록을 확인할 수 있어요.")}
  <article class="report-placeholder"><span class="kiosk-kicker">MIRRORTING WORKS · 퇴근 리포트</span><h2>아직 연결된 체험 기록이 없어요.</h2><dl><div><dt>사원 정보</dt><dd>카드 확인 후 표시</dd></div><div><dt>MirrorTing 체험</dt><dd>기록 연결 후 표시</dd></div><div><dt>개인 리포트</dt><dd>체험 기록 확인 후 생성</dd></div></dl><p>기록이 없어 리포트 생성과 출력을 진행하지 않았어요.</p></article>
  ${actions(btn("home", "처음 화면으로", "", "arrow"))}`;
}

function webProcessing(s) {
  return `${step(3, "AI 프로필 만들기", false)}${heading("", s.error ? "사진을 다시<br>확인해주세요." : "AI가 사진을<br>분석하고 있어요.")}
  ${s.error ? errorPanel(s.error) + actions(errorActions(s, "ai-retry")) : `${faceMap(s.aiMode)}<div class="status-copy" role="status"><h2>${s.aiMode === "A" ? "얼굴 특징을 읽고 캐릭터와 비교해요." : "얼굴 위치를 읽고 프로필 구도를 만들어요."}</h2><p>외부 전송 없이 이 기기 안에서 분석하고 있어요.</p></div>`}`;
}

function teamSelection() {
  return `${step(1, "나의 팀 선택")}${heading("FIND YOUR TEAM", "어느 팀의 합격 문자를<br>받으셨나요?", "합격한 팀을 선택해주세요.")}
    <div class="team-grid">${teams.map((team) => `<button class="team-card" data-action="team-select" data-id="${team.id}" aria-labelledby="team-${team.id}-name team-${team.id}-action" aria-describedby="team-${team.id}-summary"><span class="team-card-heading"><strong id="team-${team.id}-name">${team.title}</strong>${teamIcon(team)}</span><span class="team-card-summary" id="team-${team.id}-summary">${team.summary}</span><span class="team-card-link"><span id="team-${team.id}-action">선택하기</span>${icon("arrow")}</span></button>`).join("")}</div>${actions(helper("선택한 팀은 사원증에 함께 표시돼요.", "badge"))}`;
}
function teamDetail(s) {
  const team = s.draftTeam;
  return `${step(1, "팀 소개")}
    <div class="team-detail-cards"><article class="team-profile" aria-labelledby="team-profile-title"><div class="team-profile-heading"><div><p class="section-label">팀 소개</p><h1 id="team-profile-title">${team.title}</h1></div>${teamIcon(team)}</div><p class="team-description">${team.description}</p><div class="keywords" aria-label="팀 키워드">${team.keywords.map((k) => `<span>#${k}</span>`).join("")}</div></article>
    <section class="team-work-card" aria-labelledby="team-work-title"><h2 id="team-work-title">주요 업무</h2><ul>${team.tasks.map((task) => `<li>${task}</li>`).join("")}</ul></section></div>${actions(btn("team-confirm", "이 팀으로 입사하기") + btn("back", "다른 팀 보기", "text", ""))}`;
}

function nameInput(s, web) {
  return `${step(2, "사원 정보 입력")}${heading("NICE TO MEET YOU", "어떤 이름으로<br>불러드릴까요?", "사원증에 들어갈 이름을 알려주세요.")}<div class="selection-summary">${teamIcon(s.team)}<div><small>함께할 팀</small><strong>${escape(s.team.title)}</strong></div></div><form id="name-form"><label class="name-label" for="visitor-name">이름</label><input class="name-input" id="visitor-name" name="name" type="text" inputmode="text" enterkeyhint="done" value="${escape(s.name)}" placeholder="이름을 입력해주세요" autocomplete="off" autocapitalize="off" spellcheck="false" aria-describedby="name-error name-count"><div class="input-meta"><span id="name-error">앞뒤 공백을 제외한 1~10자</span><span id="name-count">${Array.from(s.name).length} / 10</span></div><button type="submit" hidden>이름 확인</button></form><div class="keyboard-note">${icon("keyboard")}<span>터치로 입력하거나, 키보드를 연결해 입력할 수 있어요.</span></div><button class="touch-keyboard-open" data-action="touch-keyboard" type="button">${icon("keyboard")} 화면 키보드 열기</button>${actions(btn("name-next", "다음", "", "arrow", !s.name.trim()) + helper(web ? "입력한 이름은 사원증에 표시돼요. 처음으로 돌아가면 지워져요." : "입력한 이름은 사원증과 체험 리포트에 사용돼요."))}`;
}
function modeSelection(s) {
  return `${step(3, "AI 프로필 선택")}${heading("MEET YOUR OTHER SELF", "어떤 AI 프로필을<br>만들어볼까요?", `${escape(s.name)}님에게 어울리는 방식을 골라주세요.`)}<div class="mode-grid">${["A", "B"].map((mode) => `<button class="mode-card" data-action="mode-select" data-mode="${mode}"><span class="mode-topline"><span class="mode-letter">방식 ${mode}</span>${mode === "B" ? '<span class="mode-recommend">오늘의 추천</span>' : ""}</span>${modeArt(mode)}<h2>${modes[mode].title}</h2><p>${modes[mode].summary}</p><span class="mode-link">선택하기 ${icon("arrow")}</span></button>`).join("")}</div><p class="mode-note">촬영하기 전에는 언제든 방식을 바꿀 수 있어요.</p>`;
}
function modeDetail(s, demo) {
  const mode = modes[s.aiMode];
  const steps = s.aiMode === "A"
    ? [["얼굴 확인", "얼굴 위치와 촬영 상태를 확인해요."], ["특징 추출", "얼굴의 특징을 데이터로 변환해요."], ["캐릭터 비교", "8명의 캐릭터와 얼굴 특징을 비교해요."]]
    : [["얼굴 확인", "얼굴 위치와 사진 선명도를 확인해요."], ["구도 정리", "촬영한 옷 그대로, 얼굴이 크게 보이도록 맞춰요."], ["프로필 생성", "배경과 구도를 정리해 이미지를 만들어요."]];
  return `${step(3, "AI 프로필 선택")}${heading(`OPTION ${s.aiMode} / HOW IT WORKS`, mode.title, mode.detail)}<ol class="how-list">${steps.map(([title, copy], i) => `<li><span class="num">0${i + 1}</span><div><strong>${title}</strong><p>${copy}</p></div></li>`).join("")}</ol><p class="mode-note">${demo ? "준비된 데모 이미지로 전체 과정을 이어서 보여드려요." : s.aiMode === "A" ? "현재 촬영 준비 여부는 얼굴 감지를 기준으로 확인해요." : "사진은 외부로 보내지 않고 이 기기 안에서만 합성해요."}</p>${actions(btn("camera-open", mode.cta) + btn("back", "다른 방식 보기", "text", ""))}`;
}
function cameraScreen(s, demo) {
  return `${step(3, "프로필 촬영")}${heading("READY FOR YOUR CLOSE-UP?", demo ? "이 사진으로 시작할게요." : "화면을 바라봐주세요.", demo ? "오늘 시연은 준비된 인물 이미지로 진행해요." : "얼굴이 잘 보이면 촬영 버튼이 활성화돼요.")}<div class="camera-panel${demo ? " ready" : ""}" id="camera-panel">${demo ? '<div class="camera-sample"><img src="/assets/characters/char_01.png" alt="데모용 인물 이미지"></div>' : '<video id="camera-video" autoplay muted playsinline aria-label="카메라 프리뷰"></video>'}${faceMap(s.aiMode, true)}<span class="camera-caption"><span class="camera-dot"></span>${demo ? "데모 FaceMap" : "카메라 · AI 얼굴 감지"}</span><p class="camera-instruction" id="camera-instruction" role="status">카메라를 준비하고 있어요.</p></div><p class="camera-state-note">${demo ? "FaceMap은 실제 얼굴 감지 단계를 설명하는 시각화예요." : "촬영한 원본 이미지는 분석 후 저장하지 않아요."}</p><div id="camera-error"></div>${actions(btn("capture", demo ? "이 사진으로 계속" : "촬영하기", "", "camera", true) + btn("camera-retry", "카메라 다시 연결하기", "", "")).replace('data-action="camera-retry"', 'data-action="camera-retry" hidden')}`;
}
function processing(s, demo) {
  return `${step(3, "AI 프로필 만들기", false)}${heading("A LITTLE MOMENT OF DISCOVERY", s.error ? "프로필을 만들지<br>못했어요." : "AI 프로필을<br>만들고 있어요.")}${s.error ? statusVisual("user") : faceMap(s.aiMode)}<div class="status-copy" role="status"><h2>${s.error ? "프로필을 완성하지 못했어요." : s.aiMode === "A" ? "얼굴 특징을 읽고 캐릭터와 비교해요." : "얼굴 위치를 읽고 프로필 구도를 만들어요."}</h2><p>${s.error ? "다시 촬영하면 이어서 진행할 수 있어요." : "외부 전송 없이 이 기기 안에서 분석하고 있어요."}</p></div>${errorPanel(s.error)}${s.error ? actions(errorActions(s, "ai-retry")) : ""}`;
}
function result(s, demo) {
  return `${step(3, "나의 AI 프로필", false)}${heading("YOUR NEW IDENTITY", s.aiMode === "A" ? "나의 캐릭터를 찾았어요." : "나만의 프로필이 완성됐어요.", s.aiMode === "A" ? "8명의 캐릭터 중 가장 가까운 캐릭터예요." : "사원증에 들어갈 프로필을 확인해주세요.")}<div class="result-pass"><div class="pass-header">MIRRORTING WORKS ${logo()}</div><div class="pass-photo"><img src="${escape(s.result.image)}" alt="${demo ? "데모용 프로필 예시" : "나의 AI 프로필"}"></div><div class="pass-info"><div><h2>${escape(s.name)}</h2><p>${escape(s.team.title)}</p></div></div><div class="pass-number">MIRRORTING WORKS 사원 프로필</div></div><p class="result-explanation">${demo ? '<span class="demo-chip">샘플</span> 준비된 이미지로 보여드리는 결과예요.' : s.aiMode === "A" ? "캐릭터 간 상대적인 특징을 비교한 결과예요." : "촬영한 얼굴과 옷을 유지하고, 얼굴이 잘 보이도록 배경과 구도를 정리했어요."}</p>${errorPanel(s.error)}${actions(s.error ? errorActions(s, "nfc-open") : btn("nfc-open", s.replacingProfile ? "새 프로필로 출력 다시 준비" : "이 프로필로 사원증 만들기", "", "badge") + btn("retake", "다시 촬영하기", "text", "", s.busy) + helper(s.replacingProfile ? "카드는 이미 등록됐어요. 새 프로필만 현재 세션에 연결합니다." : "다음 단계에서 사원증 카드를 등록해요.", "nfc"))}`;
}
function nfc(s, demo, checkout = false) {
  const busy = s.busy;
  const nfcCopy = {
    waiting: "카드를 기다리고 있어요.",
    detected: "카드를 확인했어요.",
    writing: "카드를 입사 정보와 연결하고 있어요.",
    verifying: "카드 연결 상태를 확인하고 있어요.",
    resolving: "사원 정보를 확인하고 있어요.",
  };
  const title = demo
    ? checkout
      ? "퇴근 리포트를 확인할게요."
      : "사원증 등록을<br>시작할게요."
    : checkout
      ? "사원증을 태그해주세요."
      : "사원증 카드를<br>태그해주세요.";
  const ready = demo
    ? checkout
      ? "리포트를 확인할 준비가 됐어요."
      : "카드 등록 준비가 됐어요."
    : "카드를 가까이 대주세요.";
  const demoInstruction = checkout
    ? "버튼을 누르면 사원증 확인 시연이 이어져요."
    : "버튼을 누르면 카드 등록 시연이 이어져요.";
  const demoSupport = checkout
    ? "체험 기록 확인 과정을 화면에서 안전하게 확인할 수 있어요."
    : "등록 과정을 화면에서 안전하게 확인할 수 있어요.";
  return `${step(checkout ? 1 : 4, checkout ? "사원증 확인" : "사원증 카드 등록", !busy && checkout)}${heading(checkout ? "WELCOME BACK" : "MAKE IT YOURS", title, demo ? demoInstruction : "화면 아래 오른쪽 카드 리더에 올려주세요.")}${statusVisual("nfc", busy, true)}<div class="status-copy" role="status"><h2>${s.error ? "카드 확인을 마치지 못했어요." : busy ? nfcCopy[s.nfc] || nfcCopy.waiting : ready}</h2><p>${busy ? "확인이 끝날 때까지 잠시만 기다려주세요." : demo ? demoSupport : "카드는 한 장만 올려주세요."}</p></div>${!checkout ? identity(s) : ""}${errorPanel(s.error)}${actions(s.error ? errorActions(s, checkout ? "checkout-read" : "nfc-write") : btn(checkout ? "checkout-read" : "nfc-write", busy ? "카드를 확인하고 있어요" : demo ? checkout ? "리포트 확인 시연하기" : "카드 등록 시연하기" : "카드 확인하기", "", busy ? "" : "nfc", busy, busy))}`;
}
function printing(s, demo, report = false) {
  return `${step(report ? 4 : 5, report ? "퇴근 리포트 출력" : "사원증 출력", false)}${heading("A MOMENT TO TAKE WITH YOU", s.error ? s.error.code === "UNKNOWN_OUTCOME" ? "출력 결과를<br>확인하고 있어요." : "작업을 마치지<br>못했어요." : report ? "리포트를<br>준비하고 있어요." : "사원증을<br>준비하고 있어요.")}${statusVisual("printer", !s.error)}<div class="status-copy" role="status"><h2>${s.error ? "출력 작업을 확인해주세요." : demo ? "샘플 화면을 준비하고 있어요." : "서버 응답을 기다리고 있어요."}</h2><p>${demo ? "실물 출력은 진행하지 않아요." : "결과를 확인하기 전에는 다시 누르지 마세요."}</p></div>${errorPanel(s.error)}${s.error ? actions(errorActions(s, "print-retry")) : ""}`;
}
function complete(s, demo, checkout = false) {
  const status = s.printResult?.status;
  const item = checkout ? "퇴근 리포트" : "사원증";
  const title = demo ? "화면 체험을 마쳤어요." : status === "preview" ? `${item} 미리보기가 준비됐어요.` : status === "confirmed" ? "실물 출력을 확인했어요." : "출력 명령을 보냈어요.";
  const note = demo ? "샘플 데이터로 진행했으며 실물 카드 등록과 출력은 없었어요." : status === "preview" ? "서버에서 이미지를 만들었어요. 실물 프린터로는 출력하지 않았어요." : status === "confirmed" ? "현장 스태프가 종이 출력 결과를 확인했어요." : "프린터로 명령을 전송했어요. 용지 배출과 절단 완료는 현장에서 확인해주세요.";
  const preview = status === "preview" && s.printResult?.previewUrl
    ? `<a class="print-preview-link" href="${escape(s.printResult.previewUrl)}" target="_blank" rel="noopener">${item} 이미지 미리보기 열기</a>` : "";
  return `${step(5, checkout ? "퇴근 결과" : "입사 결과", false)}${heading(checkout ? "UNTIL WE MEET AGAIN" : "YOU’RE ONE OF US NOW", title, `${escape(s.name)}님, ${checkout ? "오늘의 기록을 확인해보세요." : "다음 체험으로 이어가세요."}`)}<div class="status-visual complete-visual"><div class="check-mark">${icon("check")}</div></div><div class="status-copy" role="status"><h2>${title}</h2><p>${note}</p></div>${preview}<div class="completion-route">${icon(checkout ? "receipt" : "mirror")}<div><strong>${checkout ? "퇴근 리포트" : "다음은 MirrorTing 스마트미러"}</strong><p>${checkout ? "실물 인쇄 여부를 확인한 뒤 전시 운영 안내를 따라주세요." : "등록한 카드를 가지고 스마트미러로 이동해주세요."}</p></div></div>${actions(btn("home", "처음 화면으로", "", "arrow") + (demo ? "" : '<p class="countdown"><span id="complete-count">15</span>초 뒤 처음 화면으로 돌아가요.</p>'))}`;
}
function checkoutResult(s, demo) {
  const available = s.report?.status === "available";
  const headline = demo ? s.report?.scenario : s.report?.headline?.sentence;
  const summary = demo ? s.report?.summary : s.report?.headline?.context;
  return `${step(2, "오늘의 체험 확인", !s.busy)}${heading("LOOK BACK ON YOUR DAY", `${escape(s.name)}님,<br>어떤 하루였나요?`, "MirrorTing에서 함께한 경험을 확인해보세요.")}${identity(s)}<div class="record-card"><span class="pill">${demo ? "체험용 예시 데이터" : "MirrorTing에서 받은 기록"}</span><h2>${s.busy ? "체험 기록을 불러오고 있어요." : available ? escape(headline || "체험 기록을 받았어요.") : "아직 체험 기록을 찾지 못했어요."}</h2><p>${available ? escape(summary || "아래에서 실제 리포트 항목을 확인할 수 있어요.") : s.busy ? "잠시만 기다려주세요." : "스마트미러 체험을 마쳤다면 잠시 후 다시 확인해주세요."}</p></div>${errorPanel(s.error)}${actions(available ? btn("report-open", "나의 퇴근 리포트 보기", "", "receipt") : btn("report-fetch", s.busy ? "기록을 확인하고 있어요" : "다시 확인", "", "arrow", s.busy, s.busy))}`;
}
function liveReport(s) {
  const r = s.report;
  const fitLabels = { response: "응답", voice: "목소리", expression: "표정", posture: "자세", eye: "시선" };
  const fits = Object.entries(r.fitScores || {}).filter(([key, value]) => fitLabels[key] && value && typeof value === "object");
  const list = (values) => Array.isArray(values) ? values.filter((value) => typeof value === "string" && value.trim()).map((value) => `<li>${escape(value)}</li>`).join("") : "";
  const strengths = list(r.strengths);
  const improvements = list(r.improvements);
  const coaching = Array.isArray(r.coaching) ? r.coaching.filter((item) => item && typeof item === "object" && (item.issue || item.suggestion)).map((item) => `<li>${item.issue ? `<strong>${escape(item.issue)}</strong>` : ""}${item.suggestion ? `<p>${escape(item.suggestion)}</p>` : ""}</li>`).join("") : "";
  return `${step(3, "퇴근 리포트 미리보기")}${heading("YOUR DAY, ON PAPER", "오늘의 기록을 확인해요.", "MirrorTing에서 받은 내용을 그대로 정리했어요.")}<p class="report-scroll-hint">${icon("receipt")}리포트를 위로 밀어 아래 내용도 확인해주세요.</p><article class="receipt live-receipt" tabindex="0" aria-label="MirrorTing 퇴근 리포트"><div class="receipt-brand">MIRRORTING WORKS</div><div class="receipt-label">MirrorTing 체험 리포트</div><div class="receipt-row"><span>카드 등록 정보</span><strong>${escape(s.name)} · ${escape(s.team?.title)}</strong></div><div class="receipt-row"><span>사원 번호</span><strong>${escape(s.sessionId)}</strong></div><div class="receipt-row"><span>기록 출처</span><strong>MirrorTing 세션 ${escape(r.mirrorSessionId)}</strong></div>${r.grade ? `<div class="receipt-row"><span>결과 등급</span><strong>${escape(r.grade)}</strong></div>` : ""}${typeof r.totalScore === "number" && Number.isFinite(r.totalScore) ? `<div class="receipt-row"><span>기록된 총점</span><strong>${escape(r.totalScore)}</strong></div>` : ""}<hr class="receipt-rule">${r.headline?.sentence ? `<section class="report-section"><span>오늘의 한 문장</span><p>${escape(r.headline.sentence)}</p>${r.headline.context ? `<small>${escape(r.headline.context)}</small>` : ""}</section>` : ""}${fits.length ? `<section class="report-section"><span>관찰 항목</span><div class="fit-list">${fits.map(([key, fit]) => `<div class="fit-item"><strong>${fitLabels[key]}${fit.label ? ` · ${escape(fit.label)}` : ""}${fit.provisional ? " · 참고" : ""}</strong>${fit.summary ? `<p>${escape(fit.summary)}</p>` : ""}${fit.observation ? "<small>관찰 기록이 포함돼요.</small>" : ""}</div>`).join("")}</div></section>` : ""}${strengths ? `<section class="report-section"><span>발견한 강점</span><ul>${strengths}</ul></section>` : ""}${improvements ? `<section class="report-section"><span>더 해볼 점</span><ul>${improvements}</ul></section>` : ""}${coaching ? `<section class="report-section"><span>다음 대화 제안</span><ul>${coaching}</ul></section>` : ""}${r.dayEnding?.text ? `<section class="report-section"><span>${escape(r.dayEnding.label || "오늘의 마무리")}</span><p>${escape(r.dayEnding.text)}</p></section>` : ""}<div class="receipt-end">EVERY EXPERIENCE BECOMES YOU.</div></article>${actions(btn("report-print", "이 기록으로 출력 요청", "", "printer"))}`;
}
function report(s, demo) {
  if (!demo) return liveReport(s);
  const r = s.report;
  return `${step(3, "퇴근 리포트 미리보기")}${heading("YOUR DAY, ON PAPER", "오늘의 나를 기록했어요.", demo ? "내용과 시간은 화면 확인을 위한 예시예요." : "오늘 발견한 나의 가능성을 한 장에 담았어요.")}<p class="report-scroll-hint">${icon("receipt")}리포트를 위로 밀어 아래 내용도 확인해주세요.</p><article class="receipt" tabindex="0" aria-label="퇴근 리포트 내용"><div class="receipt-brand">MIRRORTING WORKS</div><div class="receipt-label">${demo ? "체험용 예시 · " : ""}오늘의 체험 리포트</div><div class="receipt-row"><span>이름 / 팀</span><strong>${escape(s.name)} / ${escape(s.team.title)}</strong></div><div class="receipt-row"><span>사원 번호</span><strong>${escape(s.sessionId)}</strong></div>${r.checkinAt ? `<div class="receipt-row"><span>입사</span><strong>${escape(r.checkinAt)}</strong></div>` : ""}${r.checkoutAt ? `<div class="receipt-row"><span>퇴근</span><strong>${escape(r.checkoutAt)}</strong></div>` : ""}<hr class="receipt-rule">${[
    ["오늘의 시나리오", r.scenario],
    ["경험 돌아보기", r.summary],
    ["발견한 강점", r.strength],
    ["다음의 나에게", r.nextAction],
  ]
    .map(([title, value]) =>
      value
        ? `<div class="report-section"><span>${title}</span><p>${escape(value)}</p></div>`
        : "",
    )
    .join(
      "",
    )}<hr class="receipt-rule">${r.modeLabel ? `<div class="receipt-row"><span>나의 프로필</span><strong>${escape(r.modeLabel)}</strong></div>` : ""}<div class="receipt-end">EVERY EXPERIENCE BECOMES YOU.</div></article>${actions(btn("report-print", "퇴근 리포트 출력", "", "printer"))}`;
}

export function renderScreen(s, demo, web = false) {
  const views = {
    home: () => home(demo, web),
    teams: teamSelection,
    team: () => teamDetail(s),
    name: () => nameInput(s, web),
    modes: () => modeSelection(s),
    detailA: () => modeDetail(s, demo),
    detailB: () => modeDetail(s, demo),
    camera: () => cameraScreen(s, demo),
    processing: () => processing(s, demo),
    resultA: () => result(s, demo),
    resultB: () => result(s, demo),
    nfc: () => nfc(s, demo),
    badge: () => printing(s, demo),
    checkinComplete: () => complete(s, demo),
    checkout: () => nfc(s, demo, true),
    checkoutResult: () => checkoutResult(s, demo),
    report: () => report(s, demo),
    reportPrint: () => printing(s, demo, true),
    checkoutComplete: () => complete(s, demo, true),
    fatal: () =>
      `${heading("WE’LL BE RIGHT BACK", "잠시 쉬어가고 있어요.", "원활한 체험을 위해 시스템을 확인하고 있어요.")}${statusVisual("alert")}<div class="status-copy" role="status"><h2>현장 스태프에게 알려주세요.</h2><p>안내에 따라 다시 시작할 수 있어요.</p></div>${actions(btn("home", "처음으로", "secondary", ""))}`,
  };
  const webViews = { home: () => webHome(demo, true), camera: () => webCamera(s), processing: () => webProcessing(s), resultA: () => webResult(s), resultB: () => webResult(s), webCard: () => webCard(s), webIssue: () => webIssue(s), webComplete, webCheckout, webReport };
  return `<section class="view">${(web && webViews[s.screen] || views[s.screen] || views.fatal)()}</section>`;
}
