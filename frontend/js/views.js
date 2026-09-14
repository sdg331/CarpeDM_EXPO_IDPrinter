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
const btn = (action, text, style = "", symbol = "arrow", disabled = false) =>
  `<button class="button ${style}" data-action="${action}" ${disabled ? "disabled" : ""}>${text}${symbol ? icon(symbol) : ""}</button>`;
const actions = (content) => `<div class="actions">${content}</div>`;
const heading = (eyebrow, title, subtitle = "") =>
  `<div class="title-group"><div class="eyebrow">${eyebrow}</div><h1>${title}</h1>${subtitle ? `<p class="subtitle">${subtitle}</p>` : ""}</div>`;
const step = (index, text, back = true) =>
  `<div class="step-row">${back ? `<button class="back" data-action="back" aria-label="이전 단계">${icon("back")}</button>` : ""}<span class="step-context"><b>${String(index).padStart(2, "0")}</b> / ${text}</span><span class="progress-rail" aria-label="전체 5단계 중 ${index}단계">${Array.from({ length: 5 }, (_, i) => `<i class="${i < index ? "done" : ""}"></i>`).join("")}</span></div>`;
const teamIcon = (team) =>
  `<span class="team-icon team-${team.id}">${icon(team.icon)}</span>`;
const helper = (text, symbol = "shield") =>
  `<p class="helper">${icon(symbol)}${text}</p>`;
const modeArt = (mode) =>
  `<div class="mode-art">${mode === "A" ? '<img src="/assets/characters/char_01.png" alt=""><img src="/assets/characters/char_03.png" alt="">' : `<div class="profile-icon">${icon("user")}</div>`}</div>`;
const identity = (s) =>
  `<div class="identity-strip">${s.result?.image ? `<img src="${escape(s.result.image)}" alt="현재 프로필">` : icon("badge")}<div><strong>${escape(s.name)}</strong><p>${escape(s.team?.title)} · ${s.aiMode ? escape(modes[s.aiMode].title) : "MIRRORTING WORKS"}</p></div><span class="pill">${escape(s.sessionId || "입사 등록 중")}</span></div>`;
const statusVisual = (symbol, working = false, nfc = false) =>
  `<div class="status-visual ${working ? "working" : ""}">${nfc ? `<div class="nfc-art">${logo()}<span>사원증</span></div>${icon("nfc", "tap-waves")}` : icon(symbol)}</div>`;
const errorPanel = (error) => {
  if (!error) return "";
  const [title, copy] = errorCopy[error.code] || errorCopy.BACKEND_UNAVAILABLE;
  return `<div class="error-box" role="alert"><h3>${title}</h3><p>${copy}</p></div>`;
};
const errorActions = (s, retry) =>
  s.error?.code === "UNKNOWN_OUTCOME"
    ? helper("현장 스태프가 처리 결과를 확인할 때까지 기다려주세요.", "info")
    : `${s.error?.retryable ? btn(retry, "다시 시도하기", "", "arrow") : ""}${btn("home", "처음으로", "secondary", "")}`;

function home() {
  return `<div class="home-head"><h1>새로운 나로,<br><span>출근해볼까요?</span></h1><p class="subtitle">AI 프로필로 만드는 나만의 사원증</p></div>
    <div class="home-visual" role="img" aria-label="AI 프로필이 담긴 사원증 예시">
      <div class="card-halo" aria-hidden="true"></div>
      <div class="sample-card sample-card-back" aria-hidden="true">${logo()}<span>MIRRORTING<br>WORKS</span></div>
      <div class="sample-card sample-card-front" aria-hidden="true"><div class="sample-card-header">MIRRORTING WORKS ${logo()}</div><div class="sample-photo"><img src="/assets/characters/char_01.png" alt=""></div><div class="sample-card-footer"><div><strong>새로운 나</strong><span>AI 프로필 예시</span></div>${icon("nfc")}</div></div>
      <div class="sample-caption" aria-hidden="true">${icon("spark")}또 다른 나를 만나는 순간</div>
    </div>
    <div class="entry-grid"><button class="entry-card primary" data-action="checkin"><span class="entry-icon">${icon("badge")}</span><span class="entry-copy"><strong>입사하기</strong><span>나만의 사원증 만들기</span></span>${icon("arrow", "entry-arrow")}</button><button class="entry-card secondary" data-action="checkout"><span class="entry-icon">${icon("logout")}</span><span class="entry-copy"><strong>퇴근하기</strong><span>오늘의 체험 리포트 받기</span></span>${icon("arrow", "entry-arrow")}</button></div><div class="home-bottom">${icon("clock")}사원증 만들기, 약 1분이면 충분해요</div>`;
}

function teamSelection() {
  return `${step(1, "나의 팀 선택")}${heading("FIND YOUR TEAM", "어느 팀에 입사하시겠어요?", "카드를 눌러 팀 소개와 주요 업무를 확인하세요.")}
    <div class="team-grid">${teams.map((team) => `<button class="team-card" data-action="team-select" data-id="${team.id}" aria-labelledby="team-${team.id}-name team-${team.id}-action" aria-describedby="team-${team.id}-summary"><span class="team-card-heading"><strong id="team-${team.id}-name">${team.title}</strong>${teamIcon(team)}</span><span class="team-card-summary" id="team-${team.id}-summary">${team.summary}</span><span class="team-card-link"><span id="team-${team.id}-action">소개 보기</span>${icon("arrow")}</span></button>`).join("")}</div>${actions(helper("선택한 팀이 사원증에 함께 표시돼요.", "badge"))}`;
}
function teamDetail(s) {
  const team = s.draftTeam;
  return `${step(1, "팀 소개")}
    <div class="team-detail-cards"><article class="team-profile" aria-labelledby="team-profile-title"><div class="team-profile-heading"><div><p class="section-label">팀 소개</p><h1 id="team-profile-title">${team.title}</h1></div>${teamIcon(team)}</div><p class="team-description">${team.description}</p><div class="keywords" aria-label="팀 키워드">${team.keywords.map((k) => `<span>#${k}</span>`).join("")}</div></article>
    <section class="team-work-card" aria-labelledby="team-work-title"><h2 id="team-work-title">주요 업무</h2><ul>${team.tasks.map((task) => `<li>${task}</li>`).join("")}</ul></section></div>${actions(btn("team-confirm", "이 팀으로 입사하기") + btn("back", "다른 팀 보기", "text", ""))}`;
}

function nameInput(s) {
  return `${step(2, "사원 정보 입력")}${heading("NICE TO MEET YOU", "어떤 이름으로<br>불러드릴까요?", "사원증에 들어갈 이름을 알려주세요.")}<div class="selection-summary">${teamIcon(s.team)}<div><small>함께할 팀</small><strong>${s.team.title}</strong></div></div><form id="name-form"><label class="name-label" for="visitor-name">이름</label><input class="name-input" id="visitor-name" name="name" type="text" value="${escape(s.name)}" placeholder="이름을 입력해주세요" autocomplete="off" autocapitalize="off" spellcheck="false" aria-describedby="name-error name-count"><div class="input-meta"><span id="name-error">앞뒤 공백을 제외한 1~10자</span><span id="name-count">${Array.from(s.name).length} / 10</span></div><button type="submit" hidden>이름 확인</button></form><div class="keyboard-note">${icon("keyboard")}<span>화면 아래의 키보드를 사용해주세요.<br>입력 후 다음 버튼을 눌러주세요.</span></div>${actions(btn("name-next", "다음", "", "arrow", !s.name.trim()) + helper("입력한 이름은 사원증과 체험 리포트에 사용돼요."))}`;
}
function modeSelection(s) {
  return `${step(3, "AI 프로필 선택")}${heading("MEET YOUR OTHER SELF", "어떤 AI 프로필을<br>만들어볼까요?", `${escape(s.name)}님만의 사원증을 완성하는 두 가지 방법.`)}<div class="mode-grid">${["A", "B"].map((mode) => `<button class="mode-card" data-action="mode-select" data-mode="${mode}"><span class="mode-letter">방식 ${mode}</span>${modeArt(mode)}<h2>${modes[mode].title}</h2><p>${modes[mode].summary}</p><span class="mode-link">어떻게 만들어지나요? ${icon("arrow")}</span></button>`).join("")}</div><p class="mode-note">두 가지 중 한 가지를 선택해주세요.<br>촬영하기 전에는 언제든 변경할 수 있어요.</p>`;
}
function modeDetail(s, demo) {
  const mode = modes[s.aiMode];
  return `${step(3, "AI 프로필 선택")}${heading(`OPTION ${s.aiMode} / HOW IT WORKS`, mode.title, mode.detail)}<ol class="how-list">${mode.steps.map(([title, copy], i) => `<li><span class="num">0${i + 1}</span><div><strong>${title}</strong><p>${copy}</p></div></li>`).join("")}</ol><p class="mode-note">${demo ? "화면 체험에서는 촬영 대신 준비된 샘플을 사용해요." : s.aiMode === "A" ? "현재 촬영 준비 여부는 얼굴 감지를 기준으로 확인해요." : "프로필 생성 기능은 서비스 연결 후 사용할 수 있어요."}</p>${actions(btn("camera-open", mode.cta) + btn("back", "다른 방식 보기", "text", ""))}`;
}
function cameraScreen(s, demo) {
  return `${step(3, "프로필 촬영")}${heading("READY FOR YOUR CLOSE-UP?", "화면을 바라봐주세요.", demo ? "카메라 없이 촬영 화면을 미리 체험하고 있어요." : "얼굴이 잘 보이면 촬영 버튼이 활성화돼요.")}<div class="camera-panel" id="camera-panel">${demo ? '<div class="camera-sample"><img src="/assets/characters/char_01.png" alt="체험용 샘플 인물"></div>' : '<video id="camera-video" autoplay muted playsinline aria-label="카메라 프리뷰"></video>'}<span class="camera-caption"><span class="camera-dot"></span>${demo ? "샘플 화면 · 실제 카메라 사용 안 함" : "카메라 프리뷰"}</span>${demo ? '<div class="camera-mark"></div>' : ""}<p class="camera-instruction" id="camera-instruction" role="status">카메라를 준비하고 있어요.</p></div><p class="camera-state-note">${demo ? "준비된 샘플로 다음 화면을 확인할 수 있어요." : "촬영한 원본 이미지는 분석 후 저장하지 않아요."}</p><div id="camera-error"></div>${actions(btn("capture", demo ? "샘플로 촬영 체험하기" : "촬영하기", "", "camera", true) + btn("camera-retry", "카메라 다시 연결하기", "secondary", "")).replace('data-action="camera-retry"', 'data-action="camera-retry" hidden')}`;
}
function processing(s, demo) {
  return `${step(3, "AI 프로필 만들기", false)}${heading("A LITTLE MOMENT OF DISCOVERY", "새로운 나를<br>만나고 있어요.")}${statusVisual("spark", !s.error)}<div class="status-copy" role="status"><h2>${s.error ? "프로필을 완성하지 못했어요." : s.aiMode === "A" ? "가장 가까운 캐릭터를 찾고 있어요." : "사원증 프로필을 만들고 있어요."}</h2><p>${s.error ? "다시 촬영하면 이어서 진행할 수 있어요." : demo ? "준비된 샘플 결과를 불러오는 중이에요." : "분석을 마칠 때까지 잠시만 기다려주세요."}</p></div>${errorPanel(s.error)}${s.error ? actions(errorActions(s, "ai-retry")) : '<div class="status-tags"><span>얼굴 특징</span><span>나만의 프로필</span><span>새로운 가능성</span></div>'}`;
}
function result(s, demo) {
  return `${step(3, "나의 AI 프로필", false)}${heading("YOUR NEW IDENTITY", s.aiMode === "A" ? "반가워요, 또 다른 나." : "나만의 프로필이 완성됐어요.", s.aiMode === "A" ? "8명의 캐릭터 중 가장 가까운 캐릭터예요." : "사원증에 들어갈 프로필을 확인해주세요.")}<div class="result-pass"><div class="pass-header">MIRRORTING WORKS ${logo()}</div><div class="pass-photo"><img src="${escape(s.result.image)}" alt="${demo ? "체험용 샘플 프로필" : "나의 AI 프로필"}"></div><div class="pass-info"><div><h2>${escape(s.name)}</h2><p>${s.team.title}</p></div><div class="barcode" aria-hidden="true"></div></div><div class="pass-number">${demo ? "체험용 샘플 · 실제 분석 결과 아님" : "MIRRORTING WORKS 사원 프로필"}</div></div><p class="result-explanation">${demo ? "화면 확인을 위한 고정 샘플이며 실제 분석 결과가 아니에요." : s.aiMode === "A" ? "캐릭터 간 상대적인 특징을 비교한 결과예요." : "촬영한 얼굴을 바탕으로 완성한 프로필이에요."}</p>${actions(btn("nfc-open", "이 프로필로 사원증 만들기", "", "badge") + helper("다음 단계에서 사원증 카드를 등록해요.", "nfc"))}`;
}
function nfc(s, demo, checkout = false) {
  const busy = s.busy;
  const nfcCopy = {
    waiting: "카드를 기다리고 있어요.",
    detected: "카드를 확인했어요.",
    writing: "사원 정보를 등록하고 있어요.",
    verifying: "등록 정보를 확인하고 있어요.",
    resolving: "사원 정보를 확인하고 있어요.",
  };
  return `${step(checkout ? 1 : 4, checkout ? "사원증 확인" : "사원증 카드 등록", !busy && checkout)}${heading(checkout ? "WELCOME BACK" : "MAKE IT YOURS", checkout ? "사원증을 태그해주세요." : "사원증 카드를<br>태그해주세요.", "화면 아래 오른쪽 카드 리더에 올려주세요.")}${statusVisual("nfc", busy, true)}<div class="status-copy" role="status"><h2>${s.error ? "카드 확인을 마치지 못했어요." : busy ? nfcCopy[s.nfc] || nfcCopy.waiting : "카드를 가까이 대주세요."}</h2><p>${busy ? "확인이 끝날 때까지 카드를 떼지 말아주세요." : demo ? "아래 버튼을 누르면 카드 태그를 체험할 수 있어요." : "카드는 한 장만 올려주세요."}</p></div>${!checkout ? identity(s) : ""}${errorPanel(s.error)}${actions(s.error ? errorActions(s, checkout ? "checkout-read" : "nfc-write") : btn(checkout ? "checkout-read" : "nfc-write", busy ? "카드를 확인하고 있어요" : demo ? "체험용 카드 태그" : "카드 확인하기", "", busy ? "" : "nfc", busy))}`;
}
function printing(s, demo, report = false) {
  return `${step(report ? 4 : 5, report ? "퇴근 리포트 출력" : "사원증 출력", false)}${heading("A MOMENT TO TAKE WITH YOU", report ? "오늘의 경험을<br>담고 있어요." : "사원증을<br>준비하고 있어요.")}${statusVisual("printer", !s.error)}<div class="status-copy" role="status"><h2>${s.error ? "출력을 마치지 못했어요." : "출력 중이에요. 잠시만 기다려주세요."}</h2><p>${demo ? "지금은 화면 체험이에요. 실제 용지는 출력되지 않아요." : "출력이 끝나면 화면 아래 왼쪽에서 받아주세요."}</p></div>${errorPanel(s.error)}${s.error ? actions(errorActions(s, "print-retry")) : `<div class="status-detail">${icon("info")} 출력이 끝날 때까지 용지를 잡아당기지 마세요.</div>`}`;
}
function complete(s, demo, checkout = false) {
  return `${step(5, checkout ? "퇴근 완료" : "입사 완료", false)}${heading(checkout ? "UNTIL WE MEET AGAIN" : "YOU’RE ONE OF US NOW", checkout ? "오늘도 수고하셨습니다." : "입사를 환영합니다.", `${escape(s.name)}님, ${checkout ? "오늘 발견한 가능성을 기억해주세요." : "MIRRORTING WORKS의 새로운 동료가 되셨네요."}`)}<div class="status-visual complete-visual"><div class="check-mark">${icon("check")}</div></div><div class="status-copy" role="status"><h2>${demo ? (checkout ? "퇴근 화면 체험을 마쳤어요." : "사원증 발급 화면 체험을 마쳤어요.") : checkout ? "퇴근 리포트 출력이 완료됐어요." : "사원증 발급이 완료됐어요."}</h2><p>${demo ? "실제 카드 등록과 출력은 진행되지 않았어요." : checkout ? "아래에서 출력된 리포트를 챙겨주세요." : "아래에서 출력된 사원증을 챙겨주세요."}</p></div><div class="completion-route">${icon(checkout ? "spark" : "mirror")}<div><strong>${checkout ? "또 다른 가능성으로 다시 만나요." : "다음은 MirrorTing 스마트미러"}</strong><p>${checkout ? "MIRRORTING WORKS에서의 하루를 함께해주셔서 고마워요." : "사원증을 가지고 스마트미러로 이동해주세요."}</p></div></div>${actions(btn("home", "처음 화면으로", "", "arrow") + '<p class="countdown"><span id="complete-count">15</span>초 뒤 처음 화면으로 돌아가요.</p>')}`;
}
function checkoutResult(s, demo) {
  const available = s.report?.status === "available";
  return `${step(2, "오늘의 체험 확인", !s.busy)}${heading("LOOK BACK ON YOUR DAY", `${escape(s.name)}님,<br>어떤 하루였나요?`, "MirrorTing에서 함께한 경험을 확인해보세요.")}${identity(s)}<div class="record-card"><span class="pill">${demo ? "체험용 예시 데이터" : "MirrorTing 체험 기록"}</span><h2>${s.busy ? "체험 기록을 불러오고 있어요." : available ? escape(s.report.scenario) : "아직 체험 기록을 찾지 못했어요."}</h2><p>${available ? escape(s.report.summary) : s.busy ? "잠시만 기다려주세요." : "스마트미러 체험을 마쳤다면 잠시 후 다시 확인해주세요."}</p></div>${errorPanel(s.error)}${actions(available ? btn("report-open", "나의 퇴근 리포트 보기", "", "receipt") : btn("report-fetch", "다시 확인", "", "arrow", s.busy))}`;
}
function report(s, demo) {
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

export function renderScreen(s, demo) {
  const views = {
    home,
    teams: teamSelection,
    team: () => teamDetail(s),
    name: () => nameInput(s),
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
  return `<section class="view">${(views[s.screen] || views.fatal)()}</section>`;
}
