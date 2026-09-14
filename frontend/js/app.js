import { createState, validateName } from "./state.js";
import { teams, scenarios, screenIds } from "./content.js";
import {
  createDemoApi,
  createLiveApi,
  KioskError,
  errorCopy,
} from "./api-client.js";
import { Camera } from "./camera.js";
import { renderScreen, escape } from "./views.js";
import { logo, icon } from "./icons.js";

const query = new URLSearchParams(location.search);
const demo = query.get("demo") === "1";
let scenario = scenarios.some(([id]) => id === query.get("scenario"))
  ? query.get("scenario")
  : "success";
let api = demo ? createDemoApi(scenario) : createLiveApi();
const state = createState();
const camera = new Camera();
const screen = document.querySelector("#screen");
const overlay = document.querySelector("#overlay");
const header = document.querySelector("#header");
const footer = document.querySelector("#footer");
let currentController;
let operationIds = new Map();
let cameraState = "uninitialized";
let cameraAttempts = 0;
let composing = false;
let lastActivity = Date.now();
let completionAt = 0;
let modal = null;
let health = "unknown";
let returnFocus = null;

function resize() {
  const kiosk = document.querySelector("#kiosk");
  const mobile = innerWidth / innerHeight < 800 / 1280;
  const scale = mobile
    ? innerWidth / 800
    : Math.min(innerWidth / 800, innerHeight / 1280);
  kiosk.style.transform = `scale(${scale})`;
  document.querySelector("#stage").style.height = mobile
    ? `${1280 * scale}px`
    : "";
}
addEventListener("resize", resize);
resize();

function render() {
  const s = state.data;
  header.innerHTML = `<div class="header-row"><div class="brand">${logo()}<span class="brand-word">MIRRORTING<br>WORKS</span></div><div class="edition"><strong>2026 EXPO</strong><br>YOUR NEXT POSSIBILITY</div></div>${demo ? '<div class="demo-line"><span>화면 체험 · 실제 촬영·카드 등록·출력 없음</span><button class="demo-settings" data-action="settings">체험 설정 ↗</button></div>' : `<div class="live-notice">${health === "unavailable" ? "서비스 연결 대기 중 · 현장 스태프에게 문의해주세요." : "나의 가능성을 발견하는 하루"}</div>`}`;
  screen.dataset.screen = screenIds[s.screen];
  screen.innerHTML = renderScreen(s, demo);
  footer.innerHTML = `<span class="footer-brand">CarpeDM <span style="font-weight:400">× 동양미래대학교</span></span><span class="footer-index">MIRRORTING WORKS / ${screenIds[s.screen].replace("SCR-", "")}</span>`;
  header.querySelector(".demo-settings")?.toggleAttribute("disabled", s.busy);
}
function go(next, patch = {}) {
  if (state.data.screen === "camera") camera.stop();
  state.invalidate();
  state.patch({ screen: next, error: null, ...patch });
  lastActivity = Date.now();
  completionAt = next.endsWith("Complete") ? Date.now() + 15000 : 0;
  render();
  screen.focus({ preventScroll: true });
  if (next === "name") {
    composing = false;
    const input = screen.querySelector("#visitor-name");
    input.focus({ preventScroll: true });
    input.setSelectionRange(input.value.length, input.value.length);
    updateName();
  }
  if (next === "camera") initializeCamera();
}
function reset() {
  currentController?.abort();
  camera.stop();
  state.reset();
  api.reset();
  operationIds.clear();
  cameraAttempts = 0;
  cameraState = "uninitialized";
  composing = false;
  completionAt = 0;
  closeModal();
  lastActivity = Date.now();
  render();
  screen.focus({ preventScroll: true });
}

// One logical operation ID per intent, reused on explicit safe retries.
async function run(
  name,
  task,
  success,
  { sideEffect = false, statusField } = {},
) {
  const token = state.begin();
  if (!token) return;
  if (!operationIds.has(name)) operationIds.set(name, crypto.randomUUID());
  const controller = new AbortController();
  currentController = controller;
  state.patch({
    error: null,
    ...(statusField
      ? { [statusField]: statusField === "nfc" ? "waiting" : "submitting" }
      : {}),
  });
  render();
  let timeout;
  const context = {
    signal: controller.signal,
    operationId: operationIds.get(name),
    onStatus: (status) => {
      const allowed =
        statusField === "nfc"
          ? ["waiting", "detected", "writing", "verifying", "resolving"]
          : ["submitting", "queued", "printing"];
      if (state.isCurrent(token) && allowed.includes(status) && statusField) {
        state.patch({ [statusField]: status });
        render();
      }
    },
  };
  try {
    const result = await Promise.race([
      task(context),
      new Promise((_, reject) => {
        timeout = setTimeout(() => {
          controller.abort();
          reject(
            new KioskError(
              sideEffect && !demo
                ? "UNKNOWN_OUTCOME"
                : name.includes("ai")
                  ? "AI_TIMEOUT"
                  : "BACKEND_UNAVAILABLE",
              !sideEffect || demo,
            ),
          );
        }, 25000);
      }),
    ]);
    if (!state.isCurrent(token)) return;
    state.finish(token);
    lastActivity = Date.now();
    success(result);
    if (state.isCurrent(token)) state.invalidate();
  } catch (error) {
    if (!state.isCurrent(token)) return;
    state.finish(token);
    state.invalidate();
    lastActivity = Date.now();
    state.patch({
      error: {
        code:
          error.code ||
          (sideEffect ? "UNKNOWN_OUTCOME" : "BACKEND_UNAVAILABLE"),
        retryable: error.retryable ?? !sideEffect,
      },
      ...(statusField ? { [statusField]: "error" } : {}),
    });
    render();
  } finally {
    clearTimeout(timeout);
    if (currentController === controller) currentController = null;
  }
}

const cameraCopy = {
  initializing: "카메라를 준비하고 있어요.",
  ready: "얼굴이 잘 보여요. 촬영할 준비가 됐어요.",
  no_person: "카메라 앞으로 조금 더 가까이 와주세요.",
  multiple_people: "한 분만 화면 안에 들어와 주세요.",
  capturing: "촬영 중이에요. 잠시만 그대로 있어주세요.",
  error: "카메라를 사용할 수 없어요.",
};
function updateCamera(status, code) {
  if (state.data.screen !== "camera" || state.data.busy) return;
  cameraState = status;
  const panel = screen.querySelector("#camera-panel");
  panel.className = `camera-panel ${status}`;
  screen.querySelector("#camera-instruction").textContent =
    code && errorCopy[code] ? errorCopy[code][0] : cameraCopy[status];
  screen.querySelector('[data-action="capture"]').disabled = status !== "ready";
  const retry = screen.querySelector('[data-action="camera-retry"]');
  retry.hidden = status !== "error";
  if (status === "error") camera.stop();
}
function initializeCamera() {
  if (demo) {
    cameraAttempts++;
    updateCamera(
      scenario === "camera_error" && cameraAttempts === 1
        ? "error"
        : scenario === "no_person"
          ? "no_person"
          : scenario === "multiple_people"
            ? "multiple_people"
            : "ready",
    );
  } else {
    camera.start(screen.querySelector("#camera-video"), api, updateCamera);
  }
}
async function capture() {
  if (cameraState !== "ready" || state.data.busy) return;
  const token = state.begin();
  cameraState = "capturing";
  screen.querySelector('[data-action="capture"]').disabled = true;
  screen.querySelector(".back").disabled = true;
  header.querySelector(".demo-settings")?.setAttribute("disabled", "");
  screen.querySelector("#camera-instruction").textContent =
    cameraCopy.capturing;
  try {
    const frame = demo
      ? new Blob(["demo fixture"], { type: "image/jpeg" })
      : await camera.capture();
    if (!state.isCurrent(token)) return;
    state.finish(token);
    go("processing", { capture: frame });
    analyze();
  } catch {
    if (!state.isCurrent(token)) return;
    state.finish(token);
    render();
    updateCamera("error");
  }
}
function analyze() {
  const s = state.data;
  run(
    "ai",
    (ctx) =>
      s.aiMode === "A"
        ? api.matchCharacter(s.capture, ctx)
        : api.generateProfile(s.capture, ctx),
    (result) => {
      if (!result || result.kind !== s.aiMode || !safeImage(result.image))
        throw new KioskError("INVALID_RESPONSE", false);
      go(s.aiMode === "A" ? "resultA" : "resultB", { result, capture: null });
    },
  );
}
function safeImage(value) {
  // Only same-origin image references; no external photo transmission or JS URLs.
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value, location.origin);
    return url.origin === location.origin && url.protocol === location.protocol;
  } catch {
    return false;
  }
}
function registerNfc() {
  const s = state.data;
  run(
    "nfc",
    (ctx) =>
      api.registerNfc(
        { name: s.name, teamId: s.team.id, aiMode: s.aiMode, result: s.result },
        ctx,
      ),
    (result) => {
      if (
        result?.status !== "verified" ||
        typeof result.sessionId !== "string" ||
        !result.sessionId
      )
        throw new KioskError("INVALID_RESPONSE", false);
      go("badge", { nfc: "success", sessionId: result.sessionId });
      print(false);
    },
    { sideEffect: true, statusField: "nfc" },
  );
}
function print(report) {
  const s = state.data;
  run(
    report ? "reportPrint" : "badge",
    (ctx) =>
      report
        ? api.printReport(s.report, ctx)
        : api.issueBadge(s.sessionId, ctx),
    (result) => {
      if (result?.status !== "success")
        throw new KioskError("UNKNOWN_OUTCOME", false);
      go(report ? "checkoutComplete" : "checkinComplete", {
        printer: "success",
      });
    },
    { sideEffect: true, statusField: "printer" },
  );
}
function readCheckout() {
  run(
    "checkout",
    (ctx) => api.resolveCheckout(ctx),
    (result) => {
      const team = teams.find((t) => t.id === result?.teamId);
      if (!team || !validateName(result?.name || "").valid || !result.sessionId)
        throw new KioskError("INVALID_RESPONSE", false);
      go("checkoutResult", {
        name: result.name,
        team,
        sessionId: result.sessionId,
        nfc: "success",
      });
      fetchReport();
    },
    { statusField: "nfc" },
  );
}
function fetchReport() {
  const s = state.data;
  run(
    "report",
    (ctx) => api.getMirrorTingReport(s.sessionId, ctx),
    (report) => {
      if (
        !report ||
        !["available", "not_found"].includes(report.status) ||
        (report.status === "available" &&
          (report.sessionId !== s.sessionId ||
            !report.reportId ||
            !report.scenario ||
            !report.summary))
      )
        throw new KioskError("INVALID_RESPONSE", false);
      state.patch({ report });
      render();
    },
  );
}

function updateName() {
  const input = screen.querySelector("#visitor-name");
  if (!input) return;
  state.patch({ name: input.value });
  const validation = validateName(input.value);
  screen.querySelector("#name-count").textContent = `${validation.length} / 10`;
  const error = screen.querySelector("#name-error");
  error.textContent =
    validation.length > 10
      ? "이름은 10자 이내로 입력해주세요."
      : "앞뒤 공백을 제외한 1~10자";
  error.classList.toggle("invalid", validation.length > 10);
  input.setAttribute("aria-invalid", String(validation.length > 10));
  screen.querySelector('[data-action="name-next"]').disabled =
    !validation.valid || composing;
}
function submitName() {
  if (composing || state.data.screen !== "name") return;
  const validation = validateName(screen.querySelector("#visitor-name").value);
  if (!validation.valid) return updateName();
  go("modes", { name: validation.name });
}
function back() {
  const s = state.data;
  if (s.busy) return;
  const previous = {
    teams: "home",
    team: "teams",
    name: "team",
    modes: "name",
    detailA: "modes",
    detailB: "modes",
    camera: s.aiMode === "A" ? "detailA" : "detailB",
    checkout: "home",
    checkoutResult: "home",
    report: "checkoutResult",
  }[s.screen];
  if (previous === "home") return reset();
  if (previous) go(previous);
}

function openModal(kind) {
  if (state.data.busy) return;
  modal = kind;
  returnFocus = document.activeElement;
  if (kind === "settings") {
    overlay.innerHTML = `<div class="overlay-backdrop"><section class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><span class="eyebrow">FRONTEND PREVIEW</span><h2 id="dialog-title">어떤 상황을 확인할까요?</h2><p>실제 장치에 요청하지 않는 화면 체험입니다.<br>상황을 바꾸면 현재 입력 정보가 초기화돼요.</p><label for="scenario">체험 시나리오</label><select id="scenario">${scenarios.map(([value, text]) => `<option value="${value}" ${scenario === value ? "selected" : ""}>${text}</option>`).join("")}</select><div class="dialog-actions"><button class="button" data-action="scenario-apply">이 상황으로 시작하기</button><button class="button secondary" data-action="modal-close">돌아가기</button></div></section></div>`;
  } else {
    overlay.innerHTML =
      '<div class="overlay-backdrop"><section class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><h2 id="dialog-title">계속 진행하시겠어요?</h2><p>잠시 사용이 없어 처음 화면으로 돌아갈 예정이에요.</p><strong class="idle-count" id="idle-count">15</strong><div class="dialog-actions"><button class="button" data-action="resume">계속하기</button><button class="button secondary" data-action="home">처음으로 돌아가기</button></div></section></div>';
  }
  header.inert = screen.inert = footer.inert = true;
  overlay.querySelector("select,button").focus();
}
function closeModal() {
  overlay.innerHTML = "";
  modal = null;
  header.inert = screen.inert = footer.inert = false;
  if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
  returnFocus = null;
}

const handlers = {
  checkin: () => {
    reset();
    go(demo && scenario === "fatal" ? "fatal" : "teams", { flow: "checkin" });
  },
  checkout: () => {
    reset();
    go("checkout", { flow: "checkout" });
  },
  "team-select": (el) => {
    const team = teams.find((t) => t.id === el.dataset.id);
    if (team) go("team", { draftTeam: team });
  },
  "team-confirm": () => go("name", { team: state.data.draftTeam }),
  "name-next": submitName,
  "mode-select": (el) => {
    if (["A", "B"].includes(el.dataset.mode))
      go(`detail${el.dataset.mode}`, { aiMode: el.dataset.mode, result: null });
  },
  "camera-open": () => go("camera"),
  "camera-retry": initializeCamera,
  capture,
  "ai-retry": () => {
    operationIds.delete("ai");
    go("camera", { capture: null });
  },
  "nfc-open": () => go("nfc"),
  "nfc-write": registerNfc,
  "checkout-read": readCheckout,
  "report-fetch": fetchReport,
  "report-open": () => {
    if (state.data.report?.status === "available") go("report");
  },
  "report-print": () => {
    go("reportPrint");
    print(true);
  },
  "print-retry": () => print(state.data.screen === "reportPrint"),
  home: reset,
  back,
  settings: () => openModal("settings"),
  "modal-close": closeModal,
  resume: () => {
    lastActivity = Date.now();
    closeModal();
  },
  "scenario-apply": () => {
    scenario = overlay.querySelector("#scenario").value;
    api = createDemoApi(scenario);
    const url = new URL(location.href);
    url.searchParams.set("scenario", scenario);
    history.replaceState(null, "", url);
    reset();
  },
};
document.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button || button.disabled || state.data.busy) return;
  handlers[button.dataset.action]?.(button);
});
document.addEventListener("input", (event) => {
  if (event.target.id === "visitor-name") updateName();
});
document.addEventListener("compositionstart", (event) => {
  if (event.target.id === "visitor-name") {
    composing = true;
    updateName();
  }
});
document.addEventListener("compositionend", (event) => {
  if (event.target.id === "visitor-name") {
    composing = false;
    updateName();
  }
});
document.addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.target.id === "name-form") submitName();
});
document.addEventListener("keydown", (event) => {
  if (event.isComposing || event.keyCode === 229) return;
  if (modal && event.key === "Tab") {
    const focusable = [...overlay.querySelectorAll("button,select")];
    const first = focusable[0],
      last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
  if (event.key === "Escape" && modal === "settings") closeModal();
  if (event.key === "Enter" && event.target.id === "visitor-name") {
    event.preventDefault();
    submitName();
  }
});
function activity(event) {
  lastActivity = Date.now();
  if (modal === "idle" && !event.target.closest('[data-action="home"]'))
    closeModal();
}
document.addEventListener("pointerdown", activity);
document.addEventListener("keydown", activity);
setInterval(() => {
  if (
    state.data.busy ||
    state.data.error?.code === "UNKNOWN_OUTCOME" ||
    ["home", "fatal"].includes(state.data.screen) ||
    modal === "settings"
  )
    return;
  const now = Date.now();
  if (completionAt) {
    const seconds = Math.max(0, Math.ceil((completionAt - now) / 1000));
    const count = document.querySelector("#complete-count");
    if (count) count.textContent = seconds;
    if (!seconds) reset();
    return;
  }
  if (now - lastActivity >= 60000) return reset();
  if (now - lastActivity >= 45000) {
    if (!modal) openModal("idle");
    const count = document.querySelector("#idle-count");
    if (count)
      count.textContent = Math.max(
        0,
        Math.ceil((60000 - (now - lastActivity)) / 1000),
      );
  }
}, 500);
addEventListener("pagehide", () => {
  currentController?.abort();
  camera.stop();
});
render();
if (!demo)
  api
    .getHealth()
    .then((result) => {
      health = result.ok ? "healthy" : "unavailable";
    })
    .catch(() => {
      health = "unavailable";
    })
    .finally(() => {
      // Health updates must never replace an active name input or camera element.
      if (state.data.screen === "home") render();
    });
