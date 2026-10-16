import { characters, teams, screenIds, sampleCareerTip, characterGenderOptions } from "./content.js?v=20261013-character-gender-r1";
import { createState } from "./state.js?v=20261014-face-map-r1";
import { createDigitalBadge } from "./digital-badge.js";
import { renderScreen, renderHeader, renderTeamPreview, escape } from "./views.js?v=20261016-analysis-pair-r1";
import { createLiveApi } from "./api-client.js?v=20261016-landmark-match-r1";
import { drawFaceOverlay } from "./face-overlay.js?v=20261016-analysis-pair-r1";

// Only implemented views: retired modes/detailB/resultB are not kiosk pages.
export const previewScreens = [
  ["home", "처음 화면"], ["teams", "팀 선택"],
  ["name", "이름 입력"], ["detailA", "캐릭터 매칭 안내"],
  ["camera", "촬영"], ["processing", "AI 분석"], ["resultA", "캐릭터 결과"],
  ["nfc", "입사 카드 등록"], ["badge", "사원증 출력"],
  ["checkinComplete", "입사 완료"], ["checkout", "퇴근 카드 확인"],
  ["checkoutResult", "체험 기록 확인"], ["photoCamera", "퇴근 기념사진 촬영"],
  ["photoReview", "기념사진 확인"], ["report", "퇴근 리포트"],
  ["reportPrint", "리포트 출력"], ["checkoutComplete", "퇴근 완료"], ["fatal", "서비스 점검"],
  ["souvenirCard", "사진 전용 · 카드 확인", "checkout"],
  ["souvenirCamera", "사진 전용 · 촬영", "photoCamera"],
  ["souvenirReview", "사진 전용 · 인화 확인", "photoReview"],
  ["souvenirPrint", "사진 전용 · 인화", "reportPrint"],
  ["souvenirComplete", "사진 전용 · 결과", "checkoutComplete"],
  ["webHome", "웹 · 처음 화면", "home"], ["webCamera", "웹 · 촬영", "camera"],
  ["webProcessing", "웹 · 분석", "processing"], ["webResult", "웹 · 결과", "resultA"],
  ["webIssue", "웹 · 사원증 준비"], ["webCard", "웹 · 디지털 사원증"],
  ["webComplete", "웹 · 다음 체험 안내"], ["webCheckout", "웹 · 퇴근 안내"],
  ["webReport", "웹 · 기록 없음"],
];

export function previewState(id, teamId, variant = "default", characterGender = "any") {
  const entry = previewScreens.find(([key]) => key === id) || previewScreens[0];
  const screen = entry[2] || entry[0];
  const team = teams.find(({ id }) => id === teamId) || teams[0];
  const checkout = ["checkout", "checkoutResult", "photoCamera", "photoReview", "report", "reportPrint", "checkoutComplete"].includes(screen);
  const state = {
    ...createState().data, screen, team, draftTeam: team,
    flow: checkout ? "checkout" : "checkin", name: "김미래", aiMode: "A", characterGender,
    sessionId: "UI-SAMPLE-0001", capturePreview: characters[0].image,
    souvenirPhoto: characters[0].image, digitalCard: characters[0].image,
    result: { kind: "A", characterId: characters[0].id, image: characters[0].image },
    report: {
      status: "available", sample: true, scenario: "UI 예시 · 새로운 팀원과 첫 미팅",
      careerTip: sampleCareerTip,
      summary: "화면 구성을 확인하기 위한 예시 기록입니다.",
      strength: "상대방의 이야기에 귀 기울이는 태도", nextAction: "열린 질문을 건네보세요.",
      modeLabel: "AI 캐릭터 매칭",
    },
  };
  if (["resultA", "resultB", "webIssue"].includes(screen)) state.sessionId = null;
  if (id.startsWith("souvenir")) Object.assign(state, { flow: "souvenir", name: "", sessionId: null, photoGrant: { photoPass: "SAMPLE-PHOTO", sample: true } });
  if (variant === "loading") Object.assign(state, { busy: true, nfc: checkout ? "resolving" : "writing" });
  if (variant === "empty") state.report = { status: "not_found" };
  if (variant === "error") {
    const code = ["nfc", "checkout"].includes(screen) ? "NFC_ERROR"
      : ["badge", "reportPrint"].includes(screen) ? "PRINTER_ERROR"
      : screen === "checkoutResult" ? "REPORT_UNAVAILABLE"
      : screen === "webIssue" ? "DOWNLOAD_FAILED" : "AI_ERROR";
    state.error = { code, retryable: true };
  }
  if (variant === "unknown") state.error = { code: "UNKNOWN_OUTCOME", retryable: false };
  return { state, web: entry[0].startsWith("web"), entry };
}

if (typeof document !== "undefined") {
  const screenSelect = document.querySelector("#preview-screen");
  const teamSelect = document.querySelector("#preview-team");
  const stateSelect = document.querySelector("#preview-state");
  screenSelect.innerHTML = previewScreens.map(([id, label, screen]) =>
    `<option value="${id}">${screenIds[screen || id]} · ${label}</option>`).join("");
  teamSelect.innerHTML = teams.map(({ id, title }) => `<option value="${id}">${escape(title)}</option>`).join("");
  let badgeUrl;
  let revision = 0;
  let characterGender = "any";
  function render() {
    const currentRevision = ++revision;
    if (badgeUrl) URL.revokeObjectURL(badgeUrl);
    badgeUrl = null;
    const { state, web, entry } = previewState(screenSelect.value, teamSelect.value, stateSelect.value, characterGender);
    document.body.dataset.runtime = web ? "web" : "kiosk";
    // Preview disclosure lives in the tools above; keep the visitor chrome authentic.
    document.querySelector("#header").innerHTML = renderHeader(false, false, false, "unknown");
    const main = document.querySelector("#screen");
    main.dataset.screen = screenIds[state.screen];
    main.innerHTML = renderScreen(state.screen === "team" ? { ...state, screen: "teams" } : state, true, web);
    if (state.screen === "processing" && !state.error) {
      fetch(state.capturePreview).then(response => response.blob()).then(frame => createLiveApi().faceMap(frame))
        .then(data => {
          if (revision !== currentRevision || !data.ok) return;
          state.captureFace = data.face;
          drawFaceOverlay(main.querySelector("#analysis-face-map"), data.face, { allPoints: true });
          const note = main.querySelector("#face-feature-note");
          if (note) note.textContent = `샘플 사진에서 실제 추출한 특징점 ${data.face.landmarks.length}개`;
        }).catch(() => {});
    }
    if (state.screen === "resultA" && !state.error) {
      fetch(state.capturePreview).then(response => response.blob())
        .then(frame => createLiveApi().matchCharacter(frame, { characterGender }))
        .then(result => {
          if (revision !== currentRevision) return;
          state.result = { ...result, sample: true };
          main.innerHTML = renderScreen(state, true, web);
        }).catch(() => {});
    }
    if (state.screen === "webCard") {
      createDigitalBadge(state).then((blob) => {
        if (revision !== currentRevision) return;
        badgeUrl = URL.createObjectURL(blob);
        main.innerHTML = renderScreen({ ...state, digitalCard: badgeUrl }, true, web);
      }).catch(() => {
        if (revision === currentRevision) main.querySelector(".web-limit").textContent = "샘플 사원증 이미지를 준비하지 못했어요. 새로고침해주세요.";
      });
    }
    main.scrollTop = 0;
    document.querySelector("#overlay").innerHTML = state.screen === "team" ? renderTeamPreview(state.draftTeam) : "";
    document.querySelector("#footer").innerHTML = `<span class="footer-partner">동양미래대학교 컴퓨터공학부 전공동아리 <span class="footer-brand">CarpeDM</span></span><span class="footer-index">MIRRORTING WORKS / ${screenIds[state.screen].replace("SCR-", "")}</span>`;
    const url = new URL(location.href);
    url.searchParams.set("screen", entry[0]);
    url.searchParams.set("team", teamSelect.value);
    url.searchParams.set("state", stateSelect.value);
    url.searchParams.set("gender", characterGender);
    history.replaceState(null, "", url);
    document.querySelector("#preview-url").value = url.href;
  }
  function restore() {
    const query = new URLSearchParams(location.search);
    screenSelect.value = previewScreens.some(([id]) => id === query.get("screen")) ? query.get("screen") : "home";
    teamSelect.value = teams.some(({ id }) => id === query.get("team")) ? query.get("team") : teams[0].id;
    stateSelect.value = ["default", "loading", "error", "empty", "unknown"].includes(query.get("state")) ? query.get("state") : "default";
    characterGender = characterGenderOptions.some(([value]) => value === query.get("gender")) ? query.get("gender") : "any";
    render();
  }
  for (const control of [screenSelect, teamSelect, stateSelect]) control.addEventListener("change", render);
  document.querySelector("#preview-url").addEventListener("click", (event) => event.target.select());
  // Keep visual controls focusable for inspection without executing visitor actions.
  document.querySelector("#kiosk").addEventListener("click", (event) => {
    if (event.target.closest("button, a")) event.preventDefault();
    const preference = event.target.closest('[data-action="character-gender"]');
    const feature = event.target.closest('[data-action="face-points"]');
    if (feature) {
      const canvas = document.querySelector("#analysis-face-map");
      const shown = feature.getAttribute("aria-pressed") === "true";
      feature.setAttribute("aria-pressed", String(!shown));
      feature.textContent = `특징점 ${shown ? "보기" : "숨기기"}`;
      if (canvas) canvas.hidden = shown;
    }
    if (preference && !preference.disabled && characterGenderOptions.some(([value]) => value === preference.dataset.gender)) {
      characterGender = preference.dataset.gender;
      render();
      document.querySelector(`[data-action="character-gender"][data-gender="${characterGender}"]`)?.focus({ preventScroll: true });
    }
  });
  document.querySelector("#kiosk").addEventListener("submit", (event) => event.preventDefault());
  addEventListener("popstate", restore);
  restore();
}
