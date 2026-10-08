import { characters, teams, screenIds } from "./content.js";
import { createState } from "./state.js";
import { createDigitalBadge } from "./digital-badge.js";
import { renderScreen, renderHeader, renderTeamPreview, escape } from "./views.js?v=20261008-touch-ui-r3";

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
  ["webHome", "웹 · 처음 화면", "home"], ["webCamera", "웹 · 촬영", "camera"],
  ["webProcessing", "웹 · 분석", "processing"], ["webResult", "웹 · 결과", "resultA"],
  ["webIssue", "웹 · 사원증 준비"], ["webCard", "웹 · 디지털 사원증"],
  ["webComplete", "웹 · 다음 체험 안내"], ["webCheckout", "웹 · 퇴근 안내"],
  ["webReport", "웹 · 기록 없음"],
];

export function previewState(id, teamId, variant = "default") {
  const entry = previewScreens.find(([key]) => key === id) || previewScreens[0];
  const screen = entry[2] || entry[0];
  const team = teams.find(({ id }) => id === teamId) || teams[0];
  const checkout = ["checkout", "checkoutResult", "photoCamera", "photoReview", "report", "reportPrint", "checkoutComplete"].includes(screen);
  const state = {
    ...createState().data, screen, team, draftTeam: team,
    flow: checkout ? "checkout" : "checkin", name: "김미래", aiMode: "A",
    sessionId: "UI-SAMPLE-0001", capturePreview: characters[0].image,
    souvenirPhoto: characters[0].image, digitalCard: characters[0].image,
    result: { kind: "A", characterId: characters[0].id, image: characters[0].image },
    report: {
      status: "available", sample: true, scenario: "UI 예시 · 새로운 팀원과 첫 미팅",
      summary: "화면 구성을 확인하기 위한 예시 기록입니다.",
      strength: "상대방의 이야기에 귀 기울이는 태도", nextAction: "열린 질문을 건네보세요.",
      modeLabel: "AI 캐릭터 매칭",
    },
  };
  if (variant === "loading") Object.assign(state, { busy: true, nfc: checkout ? "resolving" : "writing" });
  if (variant === "empty") state.report = { status: "not_found" };
  if (variant === "error") {
    const code = ["nfc", "checkout"].includes(screen) ? "NFC_ERROR"
      : ["badge", "reportPrint"].includes(screen) ? "PRINTER_ERROR" : "AI_ERROR";
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
  function render() {
    const currentRevision = ++revision;
    if (badgeUrl) URL.revokeObjectURL(badgeUrl);
    badgeUrl = null;
    const { state, web, entry } = previewState(screenSelect.value, teamSelect.value, stateSelect.value);
    document.body.dataset.runtime = web ? "web" : "kiosk";
    // Preview disclosure lives in the tools above; keep the visitor chrome authentic.
    document.querySelector("#header").innerHTML = renderHeader(false, false, false, "unknown");
    const main = document.querySelector("#screen");
    main.dataset.screen = screenIds[state.screen];
    main.innerHTML = renderScreen(state.screen === "team" ? { ...state, screen: "teams" } : state, true, web);
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
    history.replaceState(null, "", url);
    document.querySelector("#preview-url").value = url.href;
  }
  function restore() {
    const query = new URLSearchParams(location.search);
    screenSelect.value = previewScreens.some(([id]) => id === query.get("screen")) ? query.get("screen") : "home";
    teamSelect.value = teams.some(({ id }) => id === query.get("team")) ? query.get("team") : teams[0].id;
    stateSelect.value = ["default", "loading", "error", "empty", "unknown"].includes(query.get("state")) ? query.get("state") : "default";
    render();
  }
  for (const control of [screenSelect, teamSelect, stateSelect]) control.addEventListener("change", render);
  document.querySelector("#preview-url").addEventListener("click", (event) => event.target.select());
  // Keep visual controls focusable for inspection without executing visitor actions.
  document.querySelector("#kiosk").addEventListener("click", (event) => {
    if (event.target.closest("button, a")) event.preventDefault();
  });
  document.querySelector("#kiosk").addEventListener("submit", (event) => event.preventDefault());
  addEventListener("popstate", restore);
  restore();
}
