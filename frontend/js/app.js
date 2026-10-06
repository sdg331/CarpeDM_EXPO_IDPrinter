import { createState, validateName } from "./state.js?v=20261005-checkout-photo";
import { teams, scenarios, screenIds } from "./content.js?v=20261005-transparent-icons";
import {
  createDemoApi,
  createLiveApi,
  isSameOriginImage,
  KioskError,
  errorCopy,
} from "./api-client.js";
import { Camera } from "./camera.js?v=20261005-audit-fixes";
import { renderScreen, renderHeader, renderTeamPreview, escape } from "./views.js?v=20261005-audit-fixes";
import { icon } from "./icons.js";
import { createMotion } from "./motion.js";
import { resolveRuntime } from "./runtime.js";
import { createDigitalBadge } from "./digital-badge.js";

const query = new URLSearchParams(location.search);
const runtime = resolveRuntime(query);
const demo = runtime === "sample";
const web = runtime === "web";
const presentation = demo || web;
document.body.dataset.runtime = runtime;
const showDemoControls = demo && query.get("controls") === "1";
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
let healthDetail = null;
let healthRequest = null;
let returnFocus = null;
let renderedScreen = null;
let badgeUrl = null;
const motion = createMotion();

function resize() {
  const kiosk = document.querySelector("#kiosk");
  if (web) {
    kiosk.style.transform = "none";
    return;
  }
  const scale = Math.min(1, innerWidth / 800, innerHeight / 1280);
  kiosk.style.transform = `scale(${scale})`;
}
addEventListener("resize", resize);
resize();

function render(direction = "forward") {
  const s = state.data;
  header.innerHTML = renderHeader(demo, web, showDemoControls, health);
  screen.dataset.screen = screenIds[s.screen];
  screen.innerHTML = renderScreen(s, demo, web);
  footer.innerHTML = `<span class="footer-brand">CarpeDM <span class="footer-partner">× 동양미래대학교</span></span><span class="footer-index">MIRRORTING WORKS / ${screenIds[s.screen].replace("SCR-", "")}</span>`;
  if (web) footer.innerHTML = `<span>CarpeDM · 2026 EXPO</span><span>로컬 웹 미리보기 · 실물 장치 미사용</span>`;
  lockHeader();
  if (renderedScreen !== s.screen) {
    motion.navigate(screen, direction);
    renderedScreen = s.screen;
  }
}
function lockHeader() {
  header.querySelectorAll(".demo-settings, .connection-button").forEach((button) => {
    button.disabled = state.data.busy;
  });
}
function refreshHealth() {
  if (demo || healthRequest) return healthRequest;
  health = "checking";
  healthDetail = null;
  healthRequest = api.getHealth()
    .then((result) => {
      health = result?.ok === true ? "healthy" : "unavailable";
      healthDetail = health === "healthy" ? result : null;
    })
    .catch(() => { health = "unavailable"; })
    .finally(() => {
      healthRequest = null;
      // Refresh status without replacing the current form, camera, or photo.
      const restoreHeaderFocus = header.contains(returnFocus);
      const headerFocused = header.contains(document.activeElement);
      header.innerHTML = renderHeader(demo, web, showDemoControls, health);
      lockHeader();
      if (restoreHeaderFocus) returnFocus = header.querySelector(".connection-button");
      if (headerFocused) header.querySelector(".connection-button")?.focus({ preventScroll: true });
      if (modal === "connections") {
        const previousFocus = returnFocus;
        const focusedIndex = [...overlay.querySelectorAll("button")].indexOf(document.activeElement);
        openModal("connections");
        returnFocus = previousFocus;
        overlay.querySelectorAll("button")[focusedIndex]?.focus({ preventScroll: true });
      }
    });
  return healthRequest;
}
function resetViewport() {
  window.scrollTo(0, 0);
  document.scrollingElement?.scrollTo(0, 0);
  screen.scrollTop = 0;
}
function go(next, patch = {}, direction = "forward") {
  if (["camera", "photoCamera"].includes(state.data.screen)) camera.stop();
  state.invalidate();
  state.patch({ screen: next, error: null, ...patch });
  lastActivity = Date.now();
  completionAt = !presentation && next.endsWith("Complete") ? Date.now() + 15000 : 0;
  render(direction);
  resetViewport();
  screen.focus({ preventScroll: true });
  if (next === "name") {
    composing = false;
    const input = screen.querySelector("#visitor-name");
    input.focus({ preventScroll: true });
    input.setSelectionRange(input.value.length, input.value.length);
    updateName();
  }
  if (["camera", "photoCamera"].includes(next)) initializeCamera();
}
function reset() {
  currentController?.abort();
  camera.stop();
  clearSouvenirPhoto();
  state.reset();
  api.reset();
  if (badgeUrl) URL.revokeObjectURL(badgeUrl);
  badgeUrl = null;
  operationIds.clear();
  cameraAttempts = 0;
  cameraState = "uninitialized";
  composing = false;
  completionAt = 0;
  closeModal();
  lastActivity = Date.now();
  render("reset");
  resetViewport();
  screen.focus({ preventScroll: true });
  refreshHealth();
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
    // A malformed response after a hardware write cannot prove that the
    // physical action did not happen. Keep the operation locked for review.
    const code = sideEffect && !demo && error?.code === "INVALID_RESPONSE"
      ? "UNKNOWN_OUTCOME"
      : error.code || (sideEffect ? "UNKNOWN_OUTCOME" : "BACKEND_UNAVAILABLE");
    state.patch({
      error: {
        code,
        ...(code === "UNKNOWN_OUTCOME" ? { operationId: context.operationId } : {}),
        retryable: code === "UNKNOWN_OUTCOME" ? false : error.retryable ?? !sideEffect,
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
  if (!["camera", "photoCamera"].includes(state.data.screen) || state.data.busy) return;
  cameraState = status;
  const panel = screen.querySelector("#camera-panel");
  panel.className = `camera-panel ${status}`;
  screen.querySelector("#camera-instruction").textContent =
    code && errorCopy[code] ? errorCopy[code][0] : cameraCopy[status];
  const captureButton = screen.querySelector('[data-action="capture"]');
  captureButton.disabled = status !== "ready";
  captureButton.hidden = status === "error";
  const retry = screen.querySelector('[data-action="camera-retry"]');
  retry.hidden = status !== "error";
  screen.querySelector(".camera-state-note").textContent = status === "error"
    ? (errorCopy[code]?.[1] || errorCopy.CAMERA_UNAVAILABLE[1])
    : demo ? "샘플 사진으로 촬영 흐름을 확인해요."
    : "촬영한 원본 이미지는 분석 후 저장하지 않아요.";
  if (state.data.screen === "photoCamera" && status !== "error")
    screen.querySelector(".camera-state-note").textContent = demo ? "샘플 사진으로 화면 흐름을 확인해요." : "사진은 이 화면의 미리보기에만 사용하고, 처음으로 돌아가면 지워요.";
  if (web && state.data.screen !== "photoCamera" && status !== "error")
    screen.querySelector(".camera-state-note").textContent = "사진은 이 컴퓨터의 AI 서버에서 처리해요. 원본은 디스크에 저장하지 않아요.";
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
    return;
  }
  camera.start(screen.querySelector("#camera-video"), api, updateCamera);
}
async function capture() {
  if (cameraState !== "ready" || state.data.busy) return;
  if (state.data.screen === "photoCamera") return captureSouvenir();
  const token = state.begin();
  cameraState = "capturing";
  screen.querySelector('[data-action="capture"]').disabled = true;
  screen.querySelector(".back").disabled = true;
  lockHeader();
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
function clearSouvenirPhoto() {
  const photo = state.data.souvenirPhoto;
  if (photo?.startsWith("blob:")) URL.revokeObjectURL(photo);
  state.patch({ souvenirPhoto: null });
}
async function captureSouvenir() {
  const token = state.begin();
  if (!token) return;
  screen.querySelector('[data-action="capture"]').disabled = true;
  screen.querySelector(".back").disabled = true;
  screen.querySelector('[data-action="photo-skip"]').disabled = true;
  lockHeader();
  try {
    const frame = demo ? null : await camera.capture();
    if (!state.isCurrent(token)) return;
    state.finish(token);
    clearSouvenirPhoto();
    go("photoReview", { souvenirPhoto: demo ? "/assets/characters/char_01.png" : URL.createObjectURL(frame) });
  } catch {
    if (!state.isCurrent(token)) return;
    state.finish(token);
    go("photoCamera");
    updateCamera("error", "CAMERA_UNAVAILABLE");
  }
}
function prepareBadge() {
  if (!web || !state.data.result) return;
  run("digital-card", ctx => createDigitalBadge(state.data, ctx), blob => {
    if (badgeUrl) URL.revokeObjectURL(badgeUrl);
    badgeUrl = URL.createObjectURL(blob);
    go("webCard", { digitalCard: badgeUrl });
  });
}
function retake() {
  if (!state.data.result) return;
  // A profile attached to a backend session is retained there until expiry.
  if (!state.data.sessionId) api.reset();
  if (badgeUrl) URL.revokeObjectURL(badgeUrl);
  badgeUrl = null;
  operationIds.delete("ai");
  operationIds.delete("digital-card");
  go("camera", { result: null, capture: null, digitalCard: null, printResult: null });
}
function analyze() {
  const s = state.data;
  run(
    "ai",
    async (ctx) => {
      return s.aiMode === "A"
        ? api.matchCharacter(s.capture, ctx)
        : api.generateProfile(s.capture, ctx);
    },
    (result) => {
      if (
        !result ||
        result.kind !== s.aiMode ||
        !isSameOriginImage(result.image, location.href)
      )
        throw new KioskError("INVALID_RESPONSE", false);
      go(s.aiMode === "A" ? "resultA" : "resultB", { result, capture: null });
    },
  );
}
function finishNfc(result, s = state.data) {
  if (result?.status !== "verified" || typeof result.sessionId !== "string" || !result.sessionId)
    throw new KioskError("INVALID_RESPONSE", false);
  if (s.result?.profileId) api.retainProfile?.(s.result.profileId);
  go("badge", { nfc: "success", sessionId: result.sessionId, replacingProfile: false });
  print(false);
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
    (result) => finishNfc(result, s),
    { sideEffect: true, statusField: "nfc" },
  );
}
function updateSessionProfile() {
  const s = state.data;
  if (!s.sessionId || s.result?.kind !== "B" || !s.result.profileId) return;
  run(
    "profileUpdate",
    (ctx) => api.updateSessionProfile(s.sessionId, s.result.profileId, ctx),
    (result) => {
      if (result?.sessionId !== s.sessionId || result?.profileId !== s.result.profileId)
        throw new KioskError("INVALID_RESPONSE", false);
      api.retainProfile?.(s.result.profileId);
      go("badge", { replacingProfile: false });
      print(false);
    },
  );
}
function finishPrint(report, result) {
  const validLiveOutput = result && {
    preview: result.physicalOutput === false && result.completionConfirmed === false && !!result.previewUrl,
    submitted: result.physicalOutput === true && result.completionConfirmed === false,
    confirmed: result.physicalOutput === true && result.completionConfirmed === true,
  }[result.status];
  if (!result || (demo ? result.status !== "success" : !validLiveOutput))
    throw new KioskError("INVALID_RESPONSE", false);
  if (result.previewUrl && !isSameOriginImage(result.previewUrl, location.href))
    throw new KioskError("INVALID_RESPONSE", false);
  if (report) clearSouvenirPhoto();
  go(report ? "checkoutComplete" : "checkinComplete", {
    printer: result.status,
    printResult: result,
  });
}
function print(report) {
  const s = state.data;
  run(
    report ? "reportPrint" : "badge",
    (ctx) =>
      report
        ? api.printReport(s.report, ctx)
        : api.issueBadge(s.sessionId, ctx),
    (result) => finishPrint(report, result),
    { sideEffect: true, statusField: "printer" },
  );
}
async function reconcileOperation() {
  const screenName = state.data.screen;
  const operationName = { nfc: "nfc", badge: "badge", reportPrint: "reportPrint" }[screenName];
  const operationId = operationIds.get(operationName);
  if (!operationId || state.data.error?.code !== "UNKNOWN_OUTCOME") return;
  const token = state.begin();
  if (!token) return;
  const controller = new AbortController();
  currentController = controller;
  state.patch({ reconciling: true });
  render();
  try {
    const operation = await api.getOperation(operationId, { signal: controller.signal });
    if (!state.isCurrent(token)) return;
    state.finish(token);
    state.patch({ reconciling: false });
    if (operation?.ok && operation.operationId === operationId && operation.status === "success") {
      if (screenName === "nfc") finishNfc(operation.result);
      else finishPrint(screenName === "reportPrint", operation.result);
      return;
    }
    if (operation?.ok && operation.operationId === operationId && operation.status === "retryable_error") {
      state.patch({ error: {
        code: operation.errorCode || (screenName === "nfc" ? "NFC_ERROR" : "PRINTER_ERROR"),
        retryable: Boolean(operation.retryable),
      } });
    }
    render();
  } catch {
    if (state.isCurrent(token)) {
      state.finish(token);
      state.patch({ reconciling: false });
      render();
    }
  } finally {
    if (currentController === controller) currentController = null;
  }
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
            typeof report.reportId !== "string" ||
            !report.reportId ||
            (!demo && (report.source !== "mirrorting" || !Number.isInteger(report.mirrorSessionId)))))
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
  const invalid = input.value.length > 0 && !validation.valid;
  error.textContent =
    validation.length > 10
      ? "이름은 10자 이내로 입력해주세요."
      : invalid ? validation.length === 0
        ? "공백을 제외한 이름을 입력해주세요."
        : "이름에 사용할 수 없는 문자가 있어요."
      : "앞뒤 공백을 제외한 1~10자";
  error.classList.toggle("invalid", invalid);
  input.setAttribute("aria-invalid", String(invalid));
  screen.querySelector('[data-action="name-next"]').disabled =
    !validation.valid || composing;
}
function submitName() {
  if (composing || state.data.screen !== "name") return;
  const validation = validateName(screen.querySelector("#visitor-name").value);
  if (!validation.valid) return updateName();
  go("detailA", { name: validation.name, aiMode: "A", result: null });
}
function back() {
  const s = state.data;
  if (s.busy) return;
  if (["resultA", "resultB"].includes(s.screen)) return retake();
  const previous = {
    teams: "home",
    team: "teams",
    name: "teams",
    detailA: "name",
    camera: s.aiMode === "A" ? "detailA" : "detailB",
    checkout: "home",
    checkoutResult: "home",
    photoCamera: "checkoutResult",
    photoReview: "photoCamera",
    report: "checkoutResult",
    webIssue: s.aiMode === "A" ? "resultA" : "resultB",
    webCheckout: "home",
    webReport: "webCheckout",
  }[s.screen];
  if (previous === "home") return reset();
  if (previous) go(previous, {}, "back");
}

function openModal(kind) {
  if (state.data.busy) return;
  modal = kind;
  returnFocus = document.activeElement;
  document.body.classList.add("modal-open");
  if (kind === "connections") {
    const checking = health === "checking";
    const cameraLabel = {
      uninitialized: "권한 요청 전",
      authorized: "권한 허용됨 · 촬영 대기",
      initializing: "연결 확인 중",
      ready: "촬영 준비됨",
      no_person: "얼굴 확인 중",
      multiple_people: "한 사람만 필요",
      capturing: "촬영 중",
      error: "연결 확인 필요",
    }[cameraState] || "권한 요청 전";
    const nfc = healthDetail?.nfc;
    const printer = healthDetail?.printer;
    const nfcLabel = demo ? "샘플 화면" : web ? "웹 미리보기에서 사용 안 함" :
      checking ? "상태 확인 중" : nfc?.backend === "mock" ? "개발용 모의 리더" : nfc?.ready ? "리더 감지 · 실물 태그 확인 필요" : "리더 연결 확인 필요";
    const printerLabel = demo ? "샘플 화면" : web ? "웹 미리보기에서 사용 안 함" :
      checking ? "상태 확인 중" : printer?.backend === "screen" ? "이미지 미리보기 · 실물 출력 없음" : printer?.ready ? "출력 설정 감지 · 용지 확인 필요" : "프린터 연결 확인 필요";
    overlay.innerHTML = `<div class="overlay-backdrop"><section class="dialog system-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><button class="system-dialog-close" data-action="modal-close" aria-label="상태 닫기">${icon("close")}</button><span class="pi-dialog-badge"><i></i> ${demo ? "SAMPLE" : web ? "WEB PREVIEW" : "DEVICE MODE"}</span><h2 id="dialog-title">현재 체험 상태</h2><p>${demo ? "준비된 데이터로 화면 흐름만 체험합니다." : web ? "카메라와 로컬 AI를 사용하며 카드 등록과 실물 출력은 진행하지 않습니다." : "기기 체험 · 장치 연결은 진행 중 확인합니다. 아래 정보는 설정 상태이며 실제 작동은 각 단계에서 확인합니다."}</p>
      <section class="system-status-group current-system" aria-labelledby="current-system-title"><div class="system-status-heading"><div><span>현재 모드</span><h3 id="current-system-title">${demo ? "샘플 체험" : web ? "로컬 웹 미리보기" : "실제 서비스 흐름"}</h3></div><strong class="status-chip ${health === "healthy" || demo ? "active" : "pending"}">${demo ? "샘플" : checking ? "확인 중" : health === "healthy" ? "서버 응답" : "확인 필요"}</strong></div><dl class="connection-list"><div><dt>로컬 AI 서버</dt><dd>${demo ? "사용 안 함" : checking ? "상태 확인 중" : health === "healthy" ? "응답 확인" : "연결 확인 필요"}</dd></div><div><dt>카메라</dt><dd>${demo ? "준비된 이미지" : cameraLabel}</dd></div><div><dt>NFC</dt><dd>${nfcLabel}</dd></div><div><dt>프린터</dt><dd>${printerLabel}</dd></div><div><dt>MirrorTing 기록</dt><dd>${demo ? "샘플 데이터" : web ? "미리보기에서 조회 안 함" : checking ? "상태 확인 중" : healthDetail?.mirrorting?.configured === false ? "스마트미러 연결 설정 필요" : "퇴근 카드 확인 후 조회"}</dd></div></dl></section>
      <p class="connection-footnote">${demo ? "이 모드에서는 촬영·AI·NFC·출력이 실제로 실행되지 않습니다." : "서버 응답이나 출력 명령 전송은 실물 출력 완료를 뜻하지 않습니다."}</p><div class="dialog-actions"><button class="button" data-action="modal-close">확인</button></div></section></div>`;
  } else if (kind === "team") {
    overlay.innerHTML = renderTeamPreview(state.data.draftTeam);
  } else if (kind === "settings") {
    overlay.innerHTML = `<div class="overlay-backdrop"><section class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><span class="eyebrow">FRONTEND PREVIEW</span><h2 id="dialog-title">어떤 상황을 확인할까요?</h2><p>실제 장치에 요청하지 않는 화면 체험입니다.<br>상황을 바꾸면 현재 입력 정보가 초기화돼요.</p><label for="scenario">체험 시나리오</label><select id="scenario">${scenarios.map(([value, text]) => `<option value="${value}" ${scenario === value ? "selected" : ""}>${text}</option>`).join("")}</select><div class="dialog-actions"><button class="button" data-action="scenario-apply">이 상황으로 시작하기</button><button class="button secondary" data-action="modal-close">돌아가기</button></div></section></div>`;
  } else {
    overlay.innerHTML =
      '<div class="overlay-backdrop"><section class="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title"><h2 id="dialog-title">계속 진행하시겠어요?</h2><p>잠시 사용이 없어 처음 화면으로 돌아갈 예정이에요.</p><strong class="idle-count" id="idle-count">15</strong><div class="dialog-actions"><button class="button" data-action="resume">계속하기</button><button class="button secondary" data-action="home">처음으로 돌아가기</button></div></section></div>';
  }
  header.inert = screen.inert = footer.inert = true;
  overlay.querySelector("select,button").focus();
}
function closeModal(restoreTeam = true) {
  if (restoreTeam && modal === "team" && state.data.screen === "team") {
    state.patch({ screen: "teams" });
    screen.dataset.screen = screenIds.teams;
  }
  motion.dismiss(overlay.querySelector(".overlay-backdrop"));
  modal = null;
  document.body.classList.remove("modal-open");
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
    go(web ? "webCheckout" : "checkout", { flow: "checkout" });
  },
  "team-select": (el) => {
    const team = teams.find((t) => t.id === el.dataset.id);
    if (team) {
      state.patch({ draftTeam: team, screen: "team" });
      screen.dataset.screen = screenIds.team;
      openModal("team");
    }
  },
  "team-confirm": () => {
    const team = state.data.draftTeam;
    if (!team) return;
    closeModal(false);
    go("name", { team });
  },
  "name-next": submitName,
  "camera-open": () => go("camera"),
  "camera-retry": initializeCamera,
  "digital-card": prepareBadge,
  "card-connect": () => { if (web && state.data.result) go("webIssue"); },
  "visit-guide": () => go("webComplete"),
  "report-preview": () => go("webReport"),
  connections: () => { refreshHealth(); openModal("connections"); },
  retake,
  capture,
  "ai-retry": () => {
    operationIds.delete("ai");
    go("camera", { capture: null });
  },
  "nfc-open": () => state.data.replacingProfile && state.data.sessionId
    ? updateSessionProfile() : go("nfc"),
  "profile-retake": () => {
    if (state.data.aiMode !== "B") return;
    if (!state.data.sessionId) operationIds.delete("nfc");
    state.patch({ replacingProfile: Boolean(state.data.sessionId) });
    retake();
  },
  "nfc-write": registerNfc,
  "checkout-read": readCheckout,
  "report-fetch": fetchReport,
  "report-open": () => {
    if (state.data.report?.status === "available") go("photoCamera");
  },
  "photo-retake": () => { clearSouvenirPhoto(); go("photoCamera"); },
  "photo-confirm": () => go("report"),
  "photo-skip": () => { clearSouvenirPhoto(); go("report"); },
  "report-print": () => {
    go("reportPrint");
    print(true);
  },
  "print-retry": () => print(state.data.screen === "reportPrint"),
  "operation-check": reconcileOperation,
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
  if (event.key === "Escape" && ["settings", "team", "connections"].includes(modal)) closeModal();
  if (event.key === "Enter" && event.target.id === "visitor-name") {
    event.preventDefault();
    submitName();
  }
});
function activity() {
  // The warning remains stable until its explicit Continue/Home action is chosen.
  if (modal === "idle") return;
  lastActivity = Date.now();
}
document.addEventListener("pointerdown", activity);
document.addEventListener("keydown", activity);
setInterval(() => {
  if (
    presentation ||
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
addEventListener("pagehide", (event) => {
  currentController?.abort();
  camera.stop();
  if (!event.persisted) { api.reset(); clearSouvenirPhoto(); }
  if (!event.persisted && badgeUrl) URL.revokeObjectURL(badgeUrl);
  motion.destroy();
});
render("reset");
refreshHealth();
