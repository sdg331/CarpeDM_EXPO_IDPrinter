import { teams, modes } from "./content.js?v=20261005-transparent-icons";
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
const kioskArtwork = (name) =>
  `<img class="kiosk-artwork" src="/assets/kiosk-icons/${name}.png" alt="" aria-hidden="true" width="1254" height="1254" decoding="async">`;

export function renderHeader(demo, web, showDemoControls, health) {
  const statusLabel = demo ? "샘플 체험 · 상태" : web ? "웹 미리보기 · 상태" : "장치 상태";
  const notice = demo
    ? `<div class="demo-line"><span><b>샘플</b> 카메라 · 카드 · 출력은 화면 체험입니다</span>${showDemoControls ? '<button class="demo-settings" data-action="settings">시연 설정</button>' : ""}</div>`
    : health === "unavailable"
      ? '<div class="live-notice" role="status">서비스 연결 대기 중 · 현장 스태프에게 문의해주세요.</div>'
      : "";
  return `<div class="header-row"><div class="brand">${logo()}<span class="brand-word">MIRRORTING<br>WORKS</span></div><button class="connection-button" data-action="connections" aria-label="${statusLabel}" aria-haspopup="dialog">${icon("info")}<span>${statusLabel}</span></button></div>${notice}`;
}

export function renderTeamPreview(team) {
  if (!team) return "";
  return `<div class="overlay-backdrop"><section class="dialog team-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="team-preview-title" aria-describedby="team-preview-description">
    <button class="team-preview-close" data-action="modal-close" aria-label="팀 설명 닫기">${icon("close")}</button>
    <div class="team-preview-hero"><div class="team-preview-image">${teamIcon(team)}</div><div class="team-preview-heading"><p class="section-label">${escape(team.english)}</p><h2 id="team-preview-title">${escape(team.title)}</h2></div><p id="team-preview-description">${escape(team.description)}</p></div>
    <div class="team-preview-content"><section aria-labelledby="team-preview-work"><p class="team-preview-label" id="team-preview-work">주요 업무</p><ul class="team-preview-tasks" role="list">${team.tasks.map((task) => `<li>${escape(task)}</li>`).join("")}</ul></section><section class="team-preview-keyword-row" aria-labelledby="team-preview-keyword"><p class="team-preview-label" id="team-preview-keyword">팀 키워드</p><div class="team-preview-keywords">${team.keywords.map((keyword) => `<span># ${escape(keyword)}</span>`).join("")}</div></section></div>
    <div class="dialog-actions team-preview-actions">${btn("team-confirm", `${escape(team.title)}으로 입사하기`)}${btn("modal-close", "다른 팀 둘러보기", "secondary", "")}</div>
  </section></div>`;
}
const helper = (text, symbol = "shield") =>
  `<p class="helper">${icon(symbol)}${text}</p>`;
const identity = (s) =>
  `<div class="identity-strip">${s.result?.image ? `<img src="${escape(s.result.image)}" alt="현재 프로필">` : icon("badge")}<div><strong>${escape(s.name)}</strong><p>${escape(s.team?.title)} · ${s.aiMode ? escape(modes[s.aiMode].title) : "MIRRORTING WORKS"}</p></div><span class="pill">${escape(s.sessionId || "입사 등록 중")}</span></div>`;
const statusVisual = (symbol, working = false, nfc = false) => {
  const artwork = nfc ? "nfc-register" : symbol === "printer" ? "thermal-printer" : null;
  return `<div class="status-visual ${artwork ? "status-art" : ""} ${working ? "working" : ""}" aria-hidden="true">${artwork ? kioskArtwork(artwork) : icon(symbol)}</div>`;
};
const analysisPhoto = (s, demo = false) => {
  if (!s.capturePreview) return statusVisual("camera", true);
  // Decorative light points; actual face detection remains on the backend.
  const points = [[46,22],[58,28],[36,34],[65,40],[43,43],[54,46],[34,52],[63,57],[47,59],[55,67],[40,72],[60,78]];
  return `<div class="analysis-photo ${demo ? "sample" : "captured"}"><img src="${escape(s.capturePreview)}" alt="${demo ? "분석 화면용 샘플 사진" : "방금 촬영한 사진"}"><div class="analysis-light" aria-hidden="true">${points.map(([x,y], i) => `<i class="analysis-point" style="--x:${x}%;--y:${y}%;--delay:-${i * 230}ms"></i>`).join("")}</div><span class="analysis-photo-label">${icon("spark")} ${demo ? "샘플 분석 화면" : "AI 분석 중"}</span></div>`;
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
  return `<div class="kiosk-welcome"><div class="welcome-copy"><p class="welcome-eyebrow">WELCOME TO MIRRORTING WORKS</p><h1>입사하신 것을<br>진심으로 축하드립니다.</h1><p class="subtitle">오늘의 직장 생활을 시작해볼까요?</p></div></div>
  <div class="kiosk-entry-actions"><button class="kiosk-entry checkin-entry" data-action="checkin" aria-label="출근하기"><span class="entry-symbol">${kioskArtwork("checkin-badge")}</span><span class="entry-content"><strong>출근하기</strong><span>나의 팀을 선택하고 사원증을 만들어요.</span></span>${icon("arrow")}</button><button class="kiosk-entry checkout-entry" data-action="checkout" aria-label="퇴근하기"><span class="entry-symbol">${kioskArtwork("checkout-report")}</span><span class="entry-content"><strong>퇴근하기</strong><span>오늘의 기록을 확인하고 기념사진을 남겨요.</span></span>${icon("arrow")}</button></div>`;
}

const cameraOverlay = (demo = false) =>
  `<div class="camera-toolbar" aria-hidden="true"><span class="camera-caption">${icon("camera")} ${demo ? "샘플 미리보기" : "카메라"}</span><span class="camera-detection" id="camera-detection">준비 중</span></div><p class="camera-instruction" id="camera-instruction" role="status">카메라를 준비하고 있어요.</p>`;

function webCamera(s) {
  return `${step(3, "사진 준비")}${heading("", "내 얼굴을 담아볼까요?", "밝은 곳에서 얼굴 전체가 보이도록 정면을 바라봐주세요.")}
  <div class="camera-panel" id="camera-panel"><video id="camera-video" autoplay muted playsinline aria-label="카메라 프리뷰"></video>${cameraOverlay()}</div>
  <p class="camera-state-note">사진은 이 기기에서 처리하고, 원본은 저장하지 않아요.</p><div id="camera-error"></div>
  ${actions(btn("capture", "이 모습으로 촬영하기", "", "camera", true) + btn("camera-retry", "카메라 다시 연결하기", "", "").replace('data-action="camera-retry"', 'data-action="camera-retry" hidden'))}`;
}

function webResult(s) {
  return `${step(3, "AI 프로필 확인")}${heading("", s.aiMode === "A" ? "나와 닮은 캐릭터예요." : "내 프로필이 완성됐어요.", "이 프로필로 나만의 사원증을 만들 수 있어요.")}
  <div class="result-pass"><div class="pass-header">MIRRORTING WORKS ${logo()}</div><div class="pass-photo"><img src="${escape(s.result.image)}" alt="이번 사진으로 처리한 AI 프로필 결과"></div><div class="pass-info"><div><h2>${escape(s.name)}</h2><p>${escape(s.team.title)}</p></div></div><div class="pass-number">2026 EXPO · 입사 프로필</div></div>
  <p class="result-explanation">${s.aiMode === "A" ? "8명의 캐릭터와 얼굴 특징을 비교한 결과예요." : "얼굴과 옷은 그대로, 얼굴이 잘 보이도록 구도를 잡았어요. 머리카락 경계는 촬영 상태에 따라 달라질 수 있어요."}</p>
  ${errorPanel(s.error)}${actions(btn("card-connect", "이 프로필로 입사하기", "", "badge", s.busy) + btn("retake", "다시 촬영하기", "text", "", s.busy))}`;
}

function webIssue(s) {
  return `${step(4, "사원증 만들기")}${heading("", "사원증을 만들 준비가 됐어요.")}
  <div class="issue-person"><img src="${escape(s.result.image)}" alt="사원증 프로필"><div><strong>${escape(s.name)}</strong><span>${escape(s.team.title)}</span></div></div>
  <p class="web-limit">미리보기에서는 카드 등록 없이 이미지만 만들어요.</p>
  ${errorPanel(s.error)}${actions(btn("digital-card", s.busy ? "만들고 있어요" : "사원증 만들기", "", "badge", s.busy, s.busy) + btn("retake", "다시 촬영하기", "text", "", s.busy))}`;
}

function webCard(s) {
  return `${step(5, "사원증 확인", false)}${heading("", "나만의 사원증이 완성됐어요.")}
  <div class="print-preview"><img class="digital-card-preview" src="${escape(s.digitalCard)}" alt="${escape(s.name)}님의 저장 가능한 사원증"></div>
  <p class="web-limit">디지털 미리보기예요. 실물 카드 등록과 출력은 하지 않았어요.</p>
  ${actions(`<a class="button" href="${escape(s.digitalCard)}" download="MIRRORTING-ID.png">사원증 저장하기</a>` + btn("visit-guide", "다음 체험 안내", "text", ""))}`;
}

function webComplete() {
  return `${heading("", "다음은,<br>MirrorTing에서 만나요.", "스마트미러 체험을 마친 뒤 이 키오스크에서 퇴근해주세요.")}
  <div class="mirror-next">${icon("mirror")}<div><span class="kiosk-kicker">02 · 스마트미러 체험</span><h2>나를 비추는 새로운 경험</h2><p>사원증 확인 → MirrorTing 체험 → 퇴근 리포트</p></div></div>
  <div class="kiosk-notice"><strong>오늘의 브라우저 시연은 여기까지예요.</strong><p>프로필과 출력 이미지는 실제로 만들었어요. 카드 등록·실물 출력·스마트미러 연결은 현장 장치가 필요해요.</p></div>
  ${actions(btn("home", "처음 화면으로", "", "arrow"))}`;
}

function webCheckout() {
  return `${step(1, "퇴근 · 사원증 확인", true, 2)}${heading("", "오늘의 체험을<br>돌아볼까요?", "사원증을 확인하면 MirrorTing 체험 리포트로 이어져요.")}
  <div class="device-step"><div class="reader-visual">${kioskArtwork("nfc-register")}</div><div><span class="device-pending">카드 리더 미연결</span><h2>사원증 확인이 필요해요.</h2><p>지금은 스마트미러 체험 기록도 연결되지 않았어요.<br>퇴근 리포트가 표시될 화면을 미리 볼 수 있어요.</p></div></div>
  ${actions(btn("report-preview", "퇴근 리포트 화면 보기", "", "receipt") + btn("home", "처음 화면으로", "text", ""))}`;
}

function webReport() {
  return `${step(2, "퇴근 · 리포트 확인", true, 2)}${heading("", "오늘의 기록이<br>리포트로 모여요.", "사원증과 스마트미러를 연결하면 체험 기록을 확인할 수 있어요.")}
  <article class="report-placeholder">${kioskArtwork("checkout-report")}<span class="kiosk-kicker">MIRRORTING WORKS · 퇴근 리포트</span><h2>아직 연결된 체험 기록이 없어요.</h2><dl><div><dt>사원 정보</dt><dd>카드 확인 후 표시</dd></div><div><dt>MirrorTing 체험</dt><dd>기록 연결 후 표시</dd></div><div><dt>개인 리포트</dt><dd>체험 기록 확인 후 생성</dd></div></dl><p>기록이 없어 리포트 생성과 출력을 진행하지 않았어요.</p></article>
  ${actions(btn("home", "처음 화면으로", "", "arrow"))}`;
}

function webProcessing(s) {
  return `${step(3, "캐릭터 분석", false)}${heading("", s.error ? "사진을 다시<br>확인해주세요." : "AI가 사진을<br>분석하고 있어요.")}
  ${s.error ? errorPanel(s.error) + actions(errorActions(s, "ai-retry")) : `${analysisPhoto(s)}<div class="status-copy" role="status"><h2>${s.aiMode === "A" ? "얼굴 특징을 읽고 캐릭터와 비교해요." : "얼굴 위치를 읽고 프로필 구도를 만들어요."}</h2><p>외부 전송 없이 이 기기 안에서 분석하고 있어요.</p></div>`}`;
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
  return `${step(2, "사원 정보 입력")}${heading("NICE TO MEET YOU", "어떤 이름으로<br>불러드릴까요?", "사원증에 들어갈 이름을 알려주세요.")}<div class="selection-summary">${teamIcon(s.team)}<div><small>함께할 팀</small><strong>${escape(s.team.title)}</strong></div></div><form id="name-form"><label class="name-label" for="visitor-name">이름</label><input class="name-input" id="visitor-name" name="name" type="text" inputmode="text" enterkeyhint="done" value="${escape(s.name)}" placeholder="이름을 입력해주세요" autocomplete="off" autocapitalize="off" spellcheck="false" aria-describedby="name-error name-count"><div class="input-meta"><span id="name-error">앞뒤 공백을 제외한 1~10자</span><span id="name-count">${Array.from(s.name).length} / 10</span></div><button type="submit" hidden>이름 확인</button></form><div class="keyboard-note">${icon("keyboard")}<span>연결된 키보드로 이름을 입력해주세요.</span></div>${actions(btn("name-next", "다음", "", "arrow", !s.name.trim()) + helper(web ? "입력한 이름은 사원증에 표시돼요. 처음으로 돌아가면 지워져요." : "입력한 이름은 사원증과 체험 리포트에 사용돼요."))}`;
}
function modeDetail(s, demo) {
  const mode = modes[s.aiMode];
  const steps = s.aiMode === "A"
    ? [["얼굴 확인", "얼굴 위치와 촬영 상태를 확인해요."], ["특징 추출", "얼굴의 특징을 데이터로 변환해요."], ["캐릭터 비교", "8명의 캐릭터와 얼굴 특징을 비교해요."]]
    : [["얼굴 확인", "얼굴 위치와 사진 선명도를 확인해요."], ["구도 정리", "촬영한 옷 그대로, 얼굴이 크게 보이도록 맞춰요."], ["프로필 생성", "배경과 구도를 정리해 이미지를 만들어요."]];
  const preview = s.aiMode === "A" ? `<section class="matching-preview" aria-label="매칭 캐릭터 미리보기"><div class="matching-preview-heading"><strong>8명의 MIRRORTING 캐릭터</strong><span>미리보기</span></div><div class="matching-portraits" aria-hidden="true">${Array.from({ length: 8 }, (_, i) => `<img src="/assets/characters/char_${String(i + 1).padStart(2, "0")}.png" alt="" width="96" height="128" decoding="async">`).join("")}</div></section>` : "";
  const stepIcons = s.aiMode === "A" ? ["user", "spark", "people"] : ["user", "camera", "badge"];
  return `${step(3, "캐릭터 매칭")}${heading("", mode.title, mode.detail)}${preview}<div class="ai-details"><ol class="how-list" aria-label="진행 과정">${steps.map(([title, copy], i) => `<li><span class="num">0${i + 1}</span><div><strong>${title}</strong><p>${copy}</p></div><span class="matching-step-icon">${icon(stepIcons[i])}</span></li>`).join("")}</ol></div><p class="mode-note">${demo ? "준비된 데모 이미지로 전체 과정을 이어서 보여드려요." : s.aiMode === "A" ? "현재 촬영 준비 여부는 얼굴 감지를 기준으로 확인해요." : "사진은 외부로 보내지 않고 이 기기 안에서만 합성해요."}</p>${actions(btn("camera-open", mode.cta) + btn("back", "이름 수정하기", "text", ""))}`;
}
function cameraScreen(s, demo) {
  return `${step(3, "프로필 촬영")}${heading("READY FOR YOUR CLOSE-UP?", demo ? "이 사진으로 시작할게요." : "화면을 바라봐주세요.", demo ? "오늘 시연은 준비된 인물 이미지로 진행해요." : "얼굴이 잘 보이면 촬영 버튼이 활성화돼요.")}<div class="camera-panel${demo ? " ready" : ""}" id="camera-panel">${demo ? '<div class="camera-sample"><img src="/assets/characters/char_01.png" alt="데모용 인물 이미지"></div>' : '<video id="camera-video" autoplay muted playsinline aria-label="카메라 프리뷰"></video>'}${cameraOverlay(demo)}</div><p class="camera-state-note">${demo ? "샘플 사진으로 촬영 흐름을 확인해요." : "촬영한 원본 이미지는 분석 후 저장하지 않아요."}</p><div id="camera-error"></div>${actions(btn("capture", demo ? "이 사진으로 계속" : "촬영하기", "", "camera", true) + btn("camera-retry", "카메라 다시 연결하기", "", "")).replace('data-action="camera-retry"', 'data-action="camera-retry" hidden')}`;
}
function processing(s, demo) {
  return `${step(3, "캐릭터 분석", false)}${heading("A LITTLE MOMENT OF DISCOVERY", s.error ? "사진을 다시<br>확인해주세요." : "닮은 캐릭터를<br>찾고 있어요.")}${s.error ? statusVisual("camera") : `${analysisPhoto(s, demo)}<div class="status-copy" role="status"><h2>${s.aiMode === "A" ? "얼굴 특징을 읽고 캐릭터와 비교해요." : "얼굴 위치를 읽고 프로필 구도를 만들어요."}</h2><p>${demo ? "준비된 샘플 데이터로 결과 화면을 보여드려요." : "외부 전송 없이 이 기기 안에서 분석하고 있어요."}</p></div>`}${errorPanel(s.error)}${s.error ? actions(errorActions(s, "ai-retry")) : ""}`;
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
  return `${step(checkout ? 1 : 4, checkout ? "사원증 확인" : "사원증 카드 등록", !busy && checkout)}${heading(checkout ? "WELCOME BACK" : "MAKE IT YOURS", s.error ? "카드 확인을<br>마치지 못했어요." : title, s.error ? "아래 안내를 확인해주세요." : demo ? demoInstruction : "화면 아래 오른쪽 카드 리더에 올려주세요.")}${statusVisual("nfc", busy, true)}${s.error ? "" : `<div class="status-copy" role="status"><h2>${busy ? nfcCopy[s.nfc] || nfcCopy.waiting : ready}</h2><p>${busy ? "확인이 끝날 때까지 잠시만 기다려주세요." : demo ? demoSupport : "카드는 한 장만 올려주세요."}</p></div>`}${!checkout ? identity(s) : ""}${errorPanel(s.error)}${actions(s.error ? errorActions(s, checkout ? "checkout-read" : "nfc-write") : btn(checkout ? "checkout-read" : "nfc-write", busy ? "카드를 확인하고 있어요" : demo ? checkout ? "리포트 확인 시연하기" : "카드 등록 시연하기" : "카드 확인하기", "", busy ? "" : "nfc", busy, busy))}`;
}
function printing(s, demo, report = false) {
  return `${step(report ? 4 : 5, report ? "퇴근 리포트 출력" : "사원증 출력", false)}${heading("A MOMENT TO TAKE WITH YOU", s.error ? s.error.code === "UNKNOWN_OUTCOME" ? "출력 결과를<br>확인하고 있어요." : "출력을 마치지<br>못했어요." : report ? "리포트를<br>준비하고 있어요." : "사원증을<br>준비하고 있어요.")}${statusVisual("printer", !s.error)}${s.error ? "" : `<div class="status-copy" role="status"><h2>${demo ? "샘플 화면을 준비하고 있어요." : "서버 응답을 기다리고 있어요."}</h2><p>${demo ? "실물 출력은 진행하지 않아요." : "결과를 확인하기 전에는 다시 누르지 마세요."}</p></div>`}${errorPanel(s.error)}${s.error ? actions(errorActions(s, "print-retry")) : ""}`;
}
function complete(s, demo, checkout = false) {
  const status = s.printResult?.status;
  const item = checkout ? "퇴근 리포트" : "사원증";
  const title = demo ? "화면 체험을 마쳤어요." : status === "preview" ? `${item} 미리보기가 준비됐어요.` : status === "confirmed" ? "실물 출력을 확인했어요." : "출력 명령을 보냈어요.";
  const note = demo ? "샘플 데이터로 진행했으며 실물 카드 등록과 출력은 없었어요." : status === "preview" ? "서버에서 이미지를 만들었어요. 실물 프린터로는 출력하지 않았어요." : status === "confirmed" ? "현장 스태프가 종이 출력 결과를 확인했어요." : "프린터로 명령을 전송했어요. 용지 배출과 절단 완료는 현장에서 확인해주세요.";
  const routeTitle = demo ? "실제 체험은 전시 부스에서" : checkout ? "퇴근 리포트" : "다음은 MirrorTing 스마트미러";
  const routeCopy = demo ? "카드 등록과 스마트미러 체험은 현장 스태프의 안내를 따라주세요." : checkout ? "실물 인쇄 여부를 확인한 뒤 전시 운영 안내를 따라주세요." : "등록한 카드를 가지고 스마트미러로 이동해주세요.";
  const preview = status === "preview" && s.printResult?.previewUrl
    ? `<a class="print-preview-link" href="${escape(s.printResult.previewUrl)}" target="_blank" rel="noopener">${item} 이미지 미리보기 열기</a>` : "";
  return `${step(5, checkout ? "퇴근 결과" : "입사 결과", false)}${heading(checkout ? "UNTIL WE MEET AGAIN" : "YOU’RE ONE OF US NOW", title, `${escape(s.name)}님, ${demo ? "샘플 화면을 모두 확인했어요." : checkout ? "오늘의 기록을 확인해보세요." : "다음 체험으로 이어가세요."}`)}<div class="status-visual complete-visual"><div class="check-mark">${icon("check")}</div></div><div class="status-copy" role="status"><p>${note}</p></div>${preview}<div class="completion-route">${icon(checkout ? "receipt" : "mirror")}<div><strong>${routeTitle}</strong><p>${routeCopy}</p></div></div>${actions(btn("home", "처음 화면으로", "", "arrow") + (demo ? "" : '<p class="countdown"><span id="complete-count">15</span>초 뒤 처음 화면으로 돌아가요.</p>'))}`;
}
function checkoutResult(s, demo) {
  const available = s.report?.status === "available";
  const headline = demo ? s.report?.scenario : s.report?.headline?.sentence;
  const summary = demo ? s.report?.summary : s.report?.headline?.context;
  return `${step(2, "오늘의 체험 확인", !s.busy)}${heading("LOOK BACK ON YOUR DAY", `${escape(s.name)}님,<br>어떤 하루였나요?`, available ? "사진은 선택이에요. 바로 리포트를 확인해도 좋아요." : "MirrorTing에서 함께한 경험을 확인해보세요.")}${identity(s)}<div class="record-card"><span class="pill">${demo ? "체험용 예시 데이터" : "MirrorTing에서 받은 기록"}</span><h2>${s.busy ? "체험 기록을 불러오고 있어요." : available ? escape(headline || "체험 기록을 받았어요.") : "아직 체험 기록을 찾지 못했어요."}</h2><p>${available ? escape(summary || "아래에서 실제 리포트 항목을 확인할 수 있어요.") : s.busy ? "잠시만 기다려주세요." : "스마트미러 체험을 마쳤다면 잠시 후 다시 확인해주세요."}</p></div>${errorPanel(s.error)}${actions(available ? btn("report-open", "기념사진 남기기", "", "camera") + btn("photo-skip", "사진 없이 리포트 보기", "text", "") : btn("report-fetch", s.busy ? "기록을 확인하고 있어요" : "다시 확인", "", "arrow", s.busy, s.busy))}`;
}
function souvenirCamera(s, demo) {
  return `${step(3, "퇴근 기념사진")}${heading("ONE LAST MEMORY", "오늘의 나를<br>한 장 남겨볼까요?", "사진은 선택이에요. 촬영하지 않아도 리포트를 확인할 수 있어요.")}<div class="camera-panel souvenir-camera" id="camera-panel">${demo ? '<div class="camera-sample"><img src="/assets/characters/char_01.png" alt="기념사진 샘플"></div>' : '<video id="camera-video" autoplay muted playsinline aria-label="기념사진 카메라 미리보기"></video>'}${cameraOverlay(demo)}</div><p class="camera-state-note">사진은 이번 리포트 화면에서만 미리 볼 수 있어요.</p><div id="camera-error"></div>${actions(btn("capture", demo ? "샘플 사진으로 계속" : "기념사진 촬영하기", "", "camera", true) + btn("camera-retry", "카메라 다시 연결하기", "secondary", "").replace('data-action="camera-retry"', 'data-action="camera-retry" hidden') + btn("photo-skip", "사진 없이 계속하기", "text", ""))}`;
}
function souvenirReview(s, demo) {
  return `${step(3, "기념사진 확인", false)}${heading("KEEP THIS MOMENT", "이 사진으로<br>기억할까요?", demo ? "실제 촬영 결과가 아닌 샘플 사진이에요." : "마음에 들지 않으면 다시 찍을 수 있어요.")}<figure class="souvenir-review"><img src="${escape(s.souvenirPhoto)}" alt="이번 방문자의 퇴근 기념사진"><figcaption>${escape(s.name)} · ${escape(s.team?.title)}</figcaption></figure><p class="photo-print-note">현재 사진은 화면 미리보기에만 들어가요. 종이 리포트에는 체험 기록만 출력돼요.</p>${actions(btn("photo-confirm", "사진과 함께 리포트 보기", "", "receipt") + btn("photo-retake", "다시 찍기", "secondary", "camera") + btn("photo-skip", "사진 없이 계속하기", "text", ""))}`;
}
function reportPhoto(s) {
  return s.souvenirPhoto ? `<figure class="receipt-photo"><img src="${escape(s.souvenirPhoto)}" alt="퇴근 기념사진 미리보기"><figcaption>오늘의 기념사진 · 화면 미리보기</figcaption></figure>` : "";
}
function reportPhotoNotice(s) {
  return s.souvenirPhoto ? '<p class="photo-print-note">사진 인쇄는 아직 연결되지 않았어요. 출력하면 체험 기록만 인쇄돼요.</p>' : "";
}
function liveReport(s) {
  const r = s.report;
  const fitLabels = { response: "응답", voice: "목소리", expression: "표정", posture: "자세", eye: "시선" };
  const fits = Object.entries(r.fitScores || {}).filter(([key, value]) => fitLabels[key] && value && typeof value === "object");
  const list = (values) => Array.isArray(values) ? values.filter((value) => typeof value === "string" && value.trim()).map((value) => `<li>${escape(value)}</li>`).join("") : "";
  const strengths = list(r.strengths);
  const improvements = list(r.improvements);
  const coaching = Array.isArray(r.coaching) ? r.coaching.filter((item) => item && typeof item === "object" && (item.issue || item.suggestion)).map((item) => `<li>${item.issue ? `<strong>${escape(item.issue)}</strong>` : ""}${item.suggestion ? `<p>${escape(item.suggestion)}</p>` : ""}</li>`).join("") : "";
  return `${step(3, "퇴근 리포트 미리보기")}${heading("YOUR DAY, ON PAPER", "오늘의 기록을 확인해요.", "MirrorTing에서 받은 내용을 그대로 정리했어요.")}<p class="report-scroll-hint">${icon("receipt")}리포트를 위로 밀어 아래 내용도 확인해주세요.</p><article class="receipt live-receipt" tabindex="0" aria-label="MirrorTing 퇴근 리포트"><div class="receipt-brand">MIRRORTING WORKS</div><div class="receipt-label">MirrorTing 체험 리포트</div>${reportPhoto(s)}<div class="receipt-row"><span>카드 등록 정보</span><strong>${escape(s.name)} · ${escape(s.team?.title)}</strong></div><div class="receipt-row"><span>사원 번호</span><strong>${escape(s.sessionId)}</strong></div><div class="receipt-row"><span>기록 출처</span><strong>MirrorTing 세션 ${escape(r.mirrorSessionId)}</strong></div>${r.grade ? `<div class="receipt-row"><span>결과 등급</span><strong>${escape(r.grade)}</strong></div>` : ""}${typeof r.totalScore === "number" && Number.isFinite(r.totalScore) ? `<div class="receipt-row"><span>기록된 총점</span><strong>${escape(r.totalScore)}</strong></div>` : ""}<hr class="receipt-rule">${r.headline?.sentence ? `<section class="report-section"><span>오늘의 한 문장</span><p>${escape(r.headline.sentence)}</p>${r.headline.context ? `<small>${escape(r.headline.context)}</small>` : ""}</section>` : ""}${fits.length ? `<section class="report-section"><span>관찰 항목</span><div class="fit-list">${fits.map(([key, fit]) => `<div class="fit-item"><strong>${fitLabels[key]}${fit.label ? ` · ${escape(fit.label)}` : ""}${fit.provisional ? " · 참고" : ""}</strong>${fit.summary ? `<p>${escape(fit.summary)}</p>` : ""}${fit.observation ? "<small>관찰 기록이 포함돼요.</small>" : ""}</div>`).join("")}</div></section>` : ""}${strengths ? `<section class="report-section"><span>발견한 강점</span><ul>${strengths}</ul></section>` : ""}${improvements ? `<section class="report-section"><span>더 해볼 점</span><ul>${improvements}</ul></section>` : ""}${coaching ? `<section class="report-section"><span>다음 대화 제안</span><ul>${coaching}</ul></section>` : ""}${r.dayEnding?.text ? `<section class="report-section"><span>${escape(r.dayEnding.label || "오늘의 마무리")}</span><p>${escape(r.dayEnding.text)}</p></section>` : ""}<div class="receipt-end">EVERY EXPERIENCE BECOMES YOU.</div></article>${reportPhotoNotice(s)}${actions(btn("report-print", s.souvenirPhoto ? "체험 기록만 출력 요청" : "이 기록으로 출력 요청", "", "printer"))}`;
}
function report(s, demo) {
  if (!demo) return liveReport(s);
  const r = s.report;
  return `${step(3, "퇴근 리포트 미리보기")}${heading("YOUR DAY, ON PAPER", "오늘의 나를 기록했어요.", demo ? "내용과 시간은 화면 확인을 위한 예시예요." : "오늘 발견한 나의 가능성을 한 장에 담았어요.")}<p class="report-scroll-hint">${icon("receipt")}리포트를 위로 밀어 아래 내용도 확인해주세요.</p><article class="receipt" tabindex="0" aria-label="퇴근 리포트 내용"><div class="receipt-brand">MIRRORTING WORKS</div><div class="receipt-label">${demo ? "체험용 예시 · " : ""}오늘의 체험 리포트</div>${reportPhoto(s)}<div class="receipt-row"><span>이름 / 팀</span><strong>${escape(s.name)} / ${escape(s.team.title)}</strong></div><div class="receipt-row"><span>사원 번호</span><strong>${escape(s.sessionId)}</strong></div>${r.checkinAt ? `<div class="receipt-row"><span>입사</span><strong>${escape(r.checkinAt)}</strong></div>` : ""}${r.checkoutAt ? `<div class="receipt-row"><span>퇴근</span><strong>${escape(r.checkoutAt)}</strong></div>` : ""}<hr class="receipt-rule">${[
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
    )}<hr class="receipt-rule">${r.modeLabel ? `<div class="receipt-row"><span>나의 프로필</span><strong>${escape(r.modeLabel)}</strong></div>` : ""}<div class="receipt-end">EVERY EXPERIENCE BECOMES YOU.</div></article>${reportPhotoNotice(s)}${actions(btn("report-print", s.souvenirPhoto ? "체험 기록만 출력 시연" : "퇴근 리포트 출력", "", "printer"))}`;
}

export function renderScreen(s, demo, web = false) {
  const views = {
    home: () => home(demo, web),
    teams: teamSelection,
    team: () => teamDetail(s),
    name: () => nameInput(s, web),

    detailA: () => modeDetail(s, demo),

    camera: () => cameraScreen(s, demo),
    processing: () => processing(s, demo),
    resultA: () => result(s, demo),

    nfc: () => nfc(s, demo),
    badge: () => printing(s, demo),
    checkinComplete: () => complete(s, demo),
    checkout: () => nfc(s, demo, true),
    checkoutResult: () => checkoutResult(s, demo),
    photoCamera: () => souvenirCamera(s, demo),
    photoReview: () => souvenirReview(s, demo),
    report: () => report(s, demo),
    reportPrint: () => printing(s, demo, true),
    checkoutComplete: () => complete(s, demo, true),
    fatal: () =>
      `${heading("WE’LL BE RIGHT BACK", "잠시 쉬어가고 있어요.", "원활한 체험을 위해 시스템을 확인하고 있어요.")}${statusVisual("alert")}<div class="status-copy" role="status"><h2>현장 스태프에게 알려주세요.</h2><p>안내에 따라 다시 시작할 수 있어요.</p></div>${actions(btn("home", "처음으로", "secondary", ""))}`,
  };
  const webViews = { home: () => webHome(demo, true), camera: () => webCamera(s), processing: () => webProcessing(s), resultA: () => webResult(s), resultB: () => webResult(s), webCard: () => webCard(s), webIssue: () => webIssue(s), webComplete, webCheckout, webReport };
  return `<section class="view">${(web && webViews[s.screen] || views[s.screen] || views.fatal)()}</section>`;
}
