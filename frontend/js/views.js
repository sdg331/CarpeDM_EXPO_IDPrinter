import { characters, teams, modes, characterGenderOptions, matchingCharacters } from "./content.js?v=20261013-character-gender-r1";
import { icon, logo } from "./icons.js";
import { errorCopy } from "./api-client.js?v=20261013-character-gender-r1";

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
  const notice = demo
    ? `<div class="demo-line"><span><b>샘플</b> 카메라 · 카드 · 출력은 화면 체험입니다</span>${showDemoControls ? '<button class="demo-settings" data-action="settings">시연 설정</button>' : ""}</div>`
    : health === "unavailable"
      ? '<div class="live-notice" role="status">서비스 연결 대기 중 · 현장 스태프에게 문의해주세요.</div>'
      : "";
  return `<div class="header-row"><div class="brand">${logo()}<span class="brand-word">MIRRORTING<br>WORKS</span></div></div>${notice}`;
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
export function renderCharacterPicker(s) {
  return `<div class="overlay-backdrop"><section class="dialog character-dialog" role="dialog" aria-modal="true" aria-labelledby="character-title"><h2 id="character-title">마음에 드는 캐릭터를 골라주세요.</h2><p>선택한 캐릭터가 사원증에 들어가요.</p><div class="character-grid">${characters.map((character) => `<button class="character-option" data-action="character-select" data-id="${character.id}" aria-label="캐릭터 ${character.id.slice(-2)} 선택" aria-pressed="${s.result?.characterId === character.id}"><img src="${character.thumbnail}" alt="" width="192" height="256"><span>캐릭터 ${character.id.slice(-2)}</span></button>`).join("")}</div><div class="dialog-actions">${btn("modal-close", "현재 캐릭터 유지하기", "secondary", "")}</div></section></div>`;
}
const characterChoice = (s) => s.aiMode === "A" && !s.sessionId && !s.error
  ? btn("character-open", "다른 캐릭터 고르기", "secondary", "", s.busy) : "";
const helper = (text, symbol = "shield") =>
  `<p class="helper">${icon(symbol)}${text}</p>`;
const identity = (s) =>
  `<div class="identity-strip">${s.result?.image ? `<img src="${escape(s.result.image)}" alt="현재 프로필">` : icon("badge")}<div><strong>${escape(s.name)}</strong><p>${escape(s.team?.title)} · ${s.aiMode ? escape(modes[s.aiMode].title) : "MIRRORTING WORKS"}</p></div><span class="pill">${escape(s.sessionId || "입사 등록 중")}</span></div>`;
const statusVisual = (symbol, working = false, nfc = false) => {
  const artwork = nfc ? "nfc-register" : { printer: "thermal-printer", camera: "photo-camera", alert: "service-alert" }[symbol];
  return `<div class="status-visual ${artwork ? "status-art" : ""} ${working ? "working" : ""}" aria-hidden="true">${artwork ? kioskArtwork(artwork) : icon(symbol)}</div>`;
};
const analysisPhoto = (s, demo = false) => {
  if (!s.capturePreview) return statusVisual("camera", true);
  const photo = `<div class="analysis-photo ${demo ? "sample" : "captured"}"><img src="${escape(s.capturePreview)}" alt="${demo ? "분석 화면용 샘플 사진" : "방금 촬영한 사진"}"><canvas class="face-overlay" id="analysis-face-map" aria-label="선택한 얼굴의 실제 특징점" hidden></canvas>${s.aiMode === "A" ? "" : `<span class="analysis-photo-label">${icon("spark")} ${demo ? "샘플 분석 화면" : "얼굴 특징 비교 중"}</span>`}</div>`;
  const comparison = s.aiMode === "A" ? `<div class="analysis-comparison"><figure class="analysis-character"><figcaption>캐릭터 미리보기</figcaption><div class="analysis-character-frames" aria-hidden="true">${matchingCharacters(s.characterGender).slice(0, 4).map((character, i) => `<img src="${character.thumbnail}" alt="" width="288" height="384" decoding="async" style="--delay:${i * 500 - 2000}ms">`).join("")}</div></figure><figure class="analysis-self"><figcaption>${demo ? "샘플 분석 화면" : "내 사진"}</figcaption>${photo}</figure></div><p class="analysis-preview-note">${matchingCharacters(s.characterGender).length}명을 비교해요. 왼쪽 4장은 추천 순서와 무관한 미리보기예요.</p>` : photo;
  return `${comparison}<div class="face-feature-controls"><p class="analysis-visual-note" id="face-feature-note">${demo ? "샘플 사진 · 실제 촬영이 아니에요." : "촬영한 얼굴의 실제 특징점을 확인하고 있어요."}</p><button type="button" class="button secondary face-feature-toggle" data-action="face-points" aria-pressed="${s.facePointsVisible !== false}">특징점 ${s.facePointsVisible === false ? "보기" : "숨기기"}</button></div>`;
};
const errorPanel = (error) => {
  if (!error) return "";
  const [title, copy] = errorCopy[error.code] || errorCopy.BACKEND_UNAVAILABLE;
  return `<div class="error-box" role="alert"><h3>${title}</h3><p>${copy}</p>${error.code === "UNKNOWN_OUTCOME" && error.operationId ? `<p class="operation-id">운영 확인용 작업 ID<br><code>${escape(error.operationId)}</code></p>` : ""}</div>`;
};
const errorActions = (s, retry) =>
  s.error?.code === "UNKNOWN_OUTCOME"
    ? btn("operation-check", s.reconciling ? "작업 상태 확인 중" : "작업 상태 다시 확인", "secondary", "info", s.reconciling, s.reconciling) + helper("결과가 불확실합니다. 현장 스태프가 실물을 확인할 때까지 재출력을 요청하지 마세요.", "info")
    : s.error?.code === "PROFILE_EXPIRED"
      ? btn("profile-retake", "프로필 다시 촬영하기", "", "camera")
    : `${s.error?.retryable ? btn(retry, "다시 시도하기", "", "arrow") : ""}${btn("home", "처음으로", "secondary", "")}`;

function home(demo, web) { return webHome(demo, web); }

function webHome(demo = false, web = false) {
  return `<div class="kiosk-welcome"><div class="welcome-copy"><h1>입사를 진심으로<br>축하합니다.</h1><p class="subtitle">당신과 함께할 오늘을 기대합니다.</p></div></div>
