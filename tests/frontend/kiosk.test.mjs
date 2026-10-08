import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { createState, validateName } from "../../frontend/js/state.js";
import {
  createLiveApi,
  createDemoApi,
  isSameOriginImage,
  normalizeMatch,
  normalizeProfile,
  request,
  KioskError,
  errorCopy,
  wait,
} from "../../frontend/js/api-client.js";
import { Camera } from "../../frontend/js/camera.js";
import { characters } from "../../frontend/js/content.js";
import { renderScreen, renderHeader, renderTeamPreview } from "../../frontend/js/views.js";
import { resolveRuntime } from "../../frontend/js/runtime.js";
import { createLiveIntegrations } from "../../frontend/js/live-integrations.js";

test("Default uses the device flow; web preview and fixtures require explicit URLs", () => {
  for (const query of ["", "scenario=success", "controls=1"])
    assert.equal(resolveRuntime(new URLSearchParams(query)), "kiosk");
  assert.equal(resolveRuntime(new URLSearchParams("kiosk=1")), "kiosk");
  assert.equal(resolveRuntime(new URLSearchParams("preview=1")), "web");
  assert.equal(resolveRuntime(new URLSearchParams("demo=1")), "web");
  assert.equal(resolveRuntime(new URLSearchParams("demo=1&scenario=ai_error")), "web");
  assert.equal(resolveRuntime(new URLSearchParams("sample=1")), "sample");
  assert.equal(resolveRuntime(new URLSearchParams("demo=1&controls=1")), "sample");
});

test("Kiosk browser presentation keeps hardware stages explicit without inventing success", () => {
  const state = { name: '<김미래>', team: { title: '디자인팀' }, aiMode: 'B', result: { image: '/api/profile/p_test/image' }, screen: 'resultB' };
  const result = renderScreen(state, false, true);
  assert.match(result, /data-action="card-connect"/);
  assert.doesNotMatch(result, /data-action="nfc-open"/);
  assert.match(result, /&lt;김미래&gt;/);
  const issue = renderScreen({ ...state, screen: 'webIssue' }, false, true);
  assert.match(issue, /카드 등록 없이/);
  assert.match(issue, /data-action="digital-card"/);
  assert.doesNotMatch(issue, /data-action="nfc-write"/);
  const card = renderScreen({ ...state, screen: 'webCard', digitalCard: 'blob:http://localhost/test' }, false, true);
  assert.match(card, /download="MIRRORTING-ID.png"/);
  assert.match(card, /실물 카드 등록과 출력은 하지 않았어요/);
});

test("Kiosk home keeps the two entry actions clear; absent records remain empty", () => {
  const home = renderScreen({ screen: 'home' }, false, true);
  assert.match(home, /data-action="checkin"/);
  assert.match(home, /data-action="checkout"/);
  assert.match(home, /입사를 진심으로<br>축하합니다\./);
  assert.match(home, /당신과 함께할 오늘을 기대합니다\./);
  assert.doesNotMatch(home, /WELCOME TO MIRRORTING WORKS|오늘, 어떤 나로|오늘의 직장 생활/);
  assert.doesNotMatch(home, /welcome-mark|pi-device-strip|kiosk-journey|pi-intro/);
  const report = renderScreen({ screen: 'webReport' }, false, true);
  assert.match(report, /아직 연결된 체험 기록이 없어요/);
  assert.doesNotMatch(report, /data-action="report-print"/);
});

test("Header omits the status button, discloses previews, and surfaces an unavailable service", () => {
  for (const health of ["unknown", "healthy", "unavailable"]) {
    const header = renderHeader(false, false, false, health);
    assert.doesNotMatch(header, /connection-button|data-action="connections"|장치 상태/);
    assert.doesNotMatch(header, /기기 체험|장치 연결은/);
    if (health === "unavailable") assert.match(header, /role="status">서비스 연결 대기 중/);
    else assert.doesNotMatch(header, /live-notice/);
  }
  assert.doesNotMatch(renderHeader(false, true, false, "healthy"), /connection-button/);
  const sample = renderHeader(true, false, true, "unknown");
  assert.doesNotMatch(sample, /connection-button/);
  assert.match(sample, /카메라 · 카드 · 출력은 화면 체험/);
  assert.match(sample, /data-action="settings"/);
});

test("Team selection opens a complete, escaped detail card before confirmation", () => {
  const team = {
    id: "design",
    iconImage: "/assets/teams/design.png",
    english: "Design",
    title: "<디자인팀>",
    description: "화면과 사용자 경험을 설계합니다.",
    tasks: ["UI·UX 디자인", "그래픽 제작", "브랜드 디자인"],
    keywords: ["UIUX", "그래픽", "디자인"],
  };
  const card = renderTeamPreview(team);
  assert.match(card, /role="dialog"/);
  assert.match(card, /&lt;디자인팀&gt;/);
  assert.match(card, /UI·UX 디자인/);
  assert.match(card, /# UIUX/);
  assert.match(card, /data-action="team-confirm"/);
  assert.match(card, /data-action="modal-close"/);
  assert.doesNotMatch(card, /<디자인팀>/);
});

test("Digital preview keeps hardware limitations without distracting device specifications", () => {
  const state = { name: '김미래', team: { title: '디자인팀' }, aiMode: 'B', result: { image: '/api/profile/p_test/image' } };
  const issue = renderScreen({ ...state, screen: 'webIssue' }, false, true);
  assert.doesNotMatch(issue, /ACR1252U|Raspberry Pi/);
  assert.match(issue, /카드 등록 없이/);
  assert.doesNotMatch(issue, /등록 완료/);
  const card = renderScreen({ ...state, screen: 'webCard', digitalCard: 'blob:http:\/\/localhost\/test' }, false, true);
  assert.match(card, /실물 카드 등록과 출력은 하지 않았어요/);
  assert.doesNotMatch(card, /ZTP-80USL2|Raspberry Pi/);
  assert.doesNotMatch(card, /출력 완료/);
});

test("Camera screen auto-starts without a separate permission button", () => {
  const camera = renderScreen({ screen: "camera", aiMode: "B" }, false, true);
  assert.match(camera, /data-action="capture"/);
  assert.match(camera, /카메라를 준비하고 있어요/);
  assert.doesNotMatch(camera, /data-action="camera-start"|카메라 켜기|카메라 허용/);
  assert.doesNotMatch(camera, /camera-facemap/);
  assert.match(camera, /aria-hidden="true"/);
  assert.doesNotMatch(camera, /photo-upload|type="file"|사진 파일로 시작하기/);
});

test("Camera status reflects detection and only a ready face enables capture", () => {
  const source = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");
  const elements = Object.fromEntries([
    "#camera-panel", "#camera-instruction", "#camera-detection", ".camera-state-note",
    '[data-action="capture"]', '[data-action="camera-retry"]',
  ].map((selector) => [selector, {}]));
  const state = createState();
  let stops = 0;
  const context = {
    state, errorCopy, demo: false, web: false,
    screen: { querySelector: (selector) => elements[selector] },
    camera: { stop: () => { stops++; } },
  };
  runInNewContext(source.slice(source.indexOf("const cameraCopy ="), source.indexOf("function initializeCamera()")), context);
  for (const screen of ["camera", "photoCamera"]) {
    state.patch({ screen });
    for (const [status, label] of [
      ["initializing", "준비 중"], ["no_person", "얼굴 확인 중"],
      ["multiple_people", "한 분씩 촬영"], ["ready", "촬영 준비 완료"],
      ["capturing", "촬영 중"], ["error", "연결 확인 필요"],
    ]) {
      runInNewContext(`updateCamera(${JSON.stringify(status)})`, context);
      assert.equal(elements["#camera-detection"].textContent, label);
      assert.equal(elements["#camera-panel"].className, `camera-panel ${status}`);
      assert.equal(elements['[data-action="capture"]'].disabled, status !== "ready");
      assert.equal(elements['[data-action="camera-retry"]'].hidden, status !== "error");
    }
  }
  assert.equal(stops, 2);
  state.patch({ busy: true });
  runInNewContext('updateCamera("ready")', context);
  assert.equal(elements['[data-action="capture"]'].disabled, true);
});

test("Checkout photo is optional and a preview never claims photo printing", () => {
  const camera = renderScreen({ screen: "photoCamera" }, false);
  assert.match(camera, /data-action="capture"/);
  assert.match(camera, /data-action="photo-skip"/);
  const state = createState();
  state.patch({ screen: "photoReview", name: "김민수", team: { title: "개발팀" }, souvenirPhoto: "blob:http://localhost/photo" });
  const review = renderScreen(state.data, false);
  assert.match(review, /data-action="photo-retake"/);
  assert.match(review, /체험 기록만 출력/);
  const report = renderScreen({ ...state.data, screen: "report", report: { fitScores: {} } }, false);
  assert.match(report, /퇴근 기념사진 미리보기/);
  assert.match(report, /사진 인쇄는 아직 연결되지/);
  assert.match(report, /체험 기록만 출력 요청/);
  const withoutPhoto = renderScreen({ ...state.data, screen: "report", souvenirPhoto: null, report: {} }, false);
  assert.doesNotMatch(withoutPhoto, /receipt-photo|퇴근 기념사진 미리보기/);
  state.reset();
  assert.equal(state.data.souvenirPhoto, null);
});

test("AI processing uses an indeterminate visual without invented progress stages", () => {
  const modeA = renderScreen({ screen: "processing", aiMode: "A", capturePreview: "blob:captured-photo" }, false, true);
  assert.match(modeA, /src="blob:captured-photo"/);
  assert.match(modeA, /analysis-light" aria-hidden="true"/);
  assert.equal((modeA.match(/class="analysis-point"/g) || []).length, 12);
  assert.doesNotMatch(modeA, /facemap|FACE MAP/);
  assert.match(modeA, /role="status"/);
  assert.match(modeA, /얼굴 특징을 읽고 캐릭터와 비교/);
  assert.doesNotMatch(modeA, /analysis-pipeline/);
  assert.doesNotMatch(modeA.replace(/<[^>]*>/g, ""), /\d+%|정확도/);

  const modeB = renderScreen({ screen: "processing", aiMode: "B" }, false, true);
  assert.match(modeB, /얼굴 위치를 읽고 프로필 구도/);
  assert.doesNotMatch(modeB, /analysis-pipeline/);
  assert.doesNotMatch(modeB, /SFace|\d+%|정확도/);
  const sample = renderScreen({ screen: "processing", aiMode: "B", capturePreview: "/assets/characters/char_01.png" }, true);
  assert.match(sample, /샘플 분석 화면/);
  const error = renderScreen({ screen: "processing", aiMode: "A", capturePreview: "blob:captured-photo", error: { code: "AI_ERROR", retryable: true } }, false);
  assert.doesNotMatch(error, /blob:captured-photo|analysis-point/);
});

test("AI preview uses the captured Blob and releases it after success, failure or cancellation", async () => {
  const source = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");
  const state = createState();
  const frame = new Blob(["actual capture"], { type: "image/jpeg" });
  const created = [], revoked = [];
  const context = {
    state, Blob, demo: false, presentation: false, cameraState: "ready",
    camera: { capture: async () => frame, stop() {} },
    URL: { createObjectURL: blob => { created.push(blob); return "blob:captured-photo"; }, revokeObjectURL: url => revoked.push(url) },
    screen: { querySelector: () => ({}), focus() {} },
    render() {}, resetViewport() {}, lockHeader() {}, updateCamera() {}, analyze() {},
    Date, crypto: { randomUUID: () => "test-ai" }, operationIds: new Map(),
    AbortController, KioskError, setTimeout, clearTimeout,
  };
  runInNewContext(source.slice(source.indexOf("function go("), source.indexOf("function reset()")) +
    source.slice(source.indexOf("async function run("), source.indexOf("const cameraCopy")) +
    source.slice(source.indexOf("function clearCapturePreview()"), source.indexOf("function clearSouvenirPhoto()")), context);
  state.patch({ screen: "camera" });
  await context.capture();
  assert.equal(created[0], frame);
  assert.equal(state.data.capture, frame);
  assert.equal(state.data.capturePreview, "blob:captured-photo");
  context.go("resultA");
  assert.deepEqual(revoked, ["blob:captured-photo"]);
  assert.equal(state.data.capture, null);
  assert.equal(state.data.capturePreview, null);
  context.clearCapturePreview();
  assert.equal(revoked.length, 1);

  state.patch({ screen: "camera" });
  await context.capture();
  await context.run("ai", async () => { throw new KioskError("AI_ERROR"); }, () => assert.fail("Unexpected success"));
  assert.equal(state.data.error.code, "AI_ERROR");
  assert.equal(state.data.capturePreview, null);
  assert.equal(state.data.capture, null);
  assert.equal(revoked.length, 2);

  state.patch({ screen: "camera" });
  context.camera.capture = async () => { state.reset(); return frame; };
  await context.capture();
  assert.equal(created.length, 2, "A late capture must not allocate a preview URL");
  assert.equal(state.data.capturePreview, null);
});

test("AI success stays visible for six seconds, while slow requests, errors and cancellation stay immediate", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const source = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");
  let now = 0, task;
  const state = createState();
  state.patch({ aiMode: "A", capture: new Blob(["frame"]) });
  const result = { kind: "A", image: "/assets/characters/char_01.png" };
  const api = { matchCharacter: async () => result, generateProfile: async () => ({ ...result, kind: "B" }) };
  const context = { state, api, wait, performance: { now: () => now }, run: (_, callback) => { task = callback; } };
  const minimum = source.match(/const MIN_AI_SCREEN_MS = \d+;/)[0];
  runInNewContext(minimum + source.slice(source.indexOf("function analyze()"), source.indexOf("function finishNfc(")) + "analyze();", context);
  let completed = false;
  const pending = task({}).then(value => { completed = true; return value; });
  await new Promise(setImmediate);
  t.mock.timers.tick(5999);
  await Promise.resolve();
  assert.equal(completed, false);
  t.mock.timers.tick(1);
  assert.equal(await pending, result);

  api.matchCharacter = async () => { now += 7000; return result; };
  assert.equal(await task({}), result);
  api.matchCharacter = async () => { throw new KioskError("AI_ERROR"); };
  await assert.rejects(task({}), { code: "AI_ERROR" });

  state.patch({ aiMode: "B" });
  const controller = new AbortController();
  const canceled = task({ signal: controller.signal });
  await new Promise(setImmediate);
  controller.abort();
  await assert.rejects(canceled, { name: "AbortError" });
});

test("Name validation trims, supports Korean/codepoints and rejects invalid lengths", () => {
  assert.equal(validateName("   ").valid, false);
  assert.deepEqual(validateName("  김미래  "), {
    name: "김미래",
    length: 3,
    valid: true,
  });
  assert.equal(validateName("가나다라마바사아자차").valid, true);
  assert.equal(validateName("가나다라마바사아자차카").valid, false);
  assert.equal(validateName("김\n미래").valid, false);
  assert.equal(validateName("😀".repeat(10)).valid, true);
});
test("Name enables Next during Korean composition and only explicit confirmation advances", () => {
  const source = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");
  const listeners = {};
  const input = { id: "visitor-name", value: "", setAttribute() {} };
  const button = { disabled: true };
  const error = { textContent: "", classList: { toggle() {} } };
  const count = { textContent: "" };
  const state = createState();
  state.patch({ screen: "name" });
  const transitions = [];
  const context = {
    validateName, state, composing: false, modal: null,
    screen: { querySelector: (selector) => ({
      "#visitor-name": input, "#name-count": count, "#name-error": error,
      '[data-action="name-next"]': button,
    })[selector] },
    document: { addEventListener: (type, callback) => { listeners[type] = callback; } },
    go: (next, patch) => transitions.push({ next, patch }),
  };
  // Exercise the actual form handlers without starting cameras or hardware.
  runInNewContext(
    source.slice(source.indexOf("function updateName()"), source.indexOf("function back()")) +
    source.slice(source.indexOf('document.addEventListener("input"'), source.indexOf("function activity()")),
    context,
  );
  const event = { target: input, preventDefault() {} };
  listeners.compositionstart(event);
  assert.equal(button.disabled, true);
  input.value = "김";
  listeners.input(event);
  assert.equal(button.disabled, false);
  assert.equal(count.textContent, "1 / 10");
  listeners.keydown({ ...event, key: "Enter", isComposing: true, keyCode: 229 });
  listeners.submit({ ...event, target: { id: "name-form" } });
  assert.equal(transitions.length, 0);
  runInNewContext("submitName()", context);
  assert.equal(transitions[0].next, "detailA");
  assert.equal(transitions[0].patch.name, "김");
  for (const value of ["", "   ", "가나다라마바사아자차카", "김\u0001"]) {
    input.value = value;
    listeners.input(event);
    assert.equal(button.disabled, true);
    runInNewContext("submitName()", context);
    assert.equal(transitions.length, 1);
  }
  input.value = "  김미래  ";
  listeners.compositionend(event);
  assert.equal(button.disabled, false);
  listeners.keydown({ ...event, key: "Enter", isComposing: false, keyCode: 13 });
  assert.equal(transitions.length, 2);
  assert.equal(transitions[1].patch.name, "김미래");
});
test("Reset isolates all visitor data and rejects late responses", () => {
  const state = createState();
  state.patch({
    screen: "nfc",
    name: "이전사용자",
    team: { id: "ai" },
    draftTeam: {},
    aiMode: "B",
    capture: new Blob(["photo"]),
    capturePreview: "blob:private-photo",
    result: { image: "photo" },
    sessionId: "private",
    nfc: "writing",
    printer: "printing",
    report: { summary: "private" },
    digitalCard: "blob:private-card",
  });
  const token = state.begin();
  state.reset();
  assert.equal(state.isCurrent(token), false);
  assert.equal(state.finish(token), false);
  for (const field of [
    "team",
    "draftTeam",
    "aiMode",
    "capture",
    "capturePreview",
    "result",
    "sessionId",
    "report",
    "digitalCard",
  ])
    assert.equal(state.data[field], null);
  assert.equal(state.data.name, "");
  assert.equal(state.data.busy, false);
});
test("Duplicate intent is locked and old operations cannot release a new lock", () => {
  const state = createState();
  const previous = state.begin();
  assert.equal(state.begin(), null);
  state.invalidate();
  const next = state.begin();
  assert.equal(state.finish(previous), false);
  assert.equal(state.data.busy, true);
  assert.equal(state.finish(next), true);
});
test("Navigation invalidates a response even before session reset", () => {
  const state = createState();
  state.patch({ screen: "processing" });
  const token = state.begin();
  state.patch({ screen: "home" });
  assert.equal(state.isCurrent(token), false);
});
test("A real backend outage never becomes a sample result", async () => {
  const api = createLiveApi({}, async () => {
    throw new TypeError("offline");
  });
  await assert.rejects(api.matchCharacter(new Blob(["test"])), {
    code: "BACKEND_UNAVAILABLE",
  });
  assert.equal(api.demo, false);
});
test("Only known character results are accepted; diagnostic scores stay out of UI", () => {
  const actual = normalizeMatch({
    ok: true,
    top: 0,
    characters: [{ id: "char_01", image: "https://untrusted.example/photo" }],
    raw: [123],
    margin: 42,
  });
  assert.deepEqual(actual, {
    kind: "A",
    characterId: "char_01",
    image: characters[0].image,
  });
  assert.throws(() => normalizeMatch({ ok: true, top: 20, characters: [] }), {
    code: "INVALID_RESPONSE",
  });
  assert.throws(() => normalizeMatch({ ok: false, error: "no_face" }), {
    code: "NO_PERSON",
  });
  assert.throws(() => normalizeMatch({ ok: false, error: "multiple_faces" }), {
    code: "MULTIPLE_PEOPLE",
  });
});
test("All 8 portraits are previewed and accepted; unknown IDs are rejected", () => {
  assert.equal(characters.length, 8);
  for (const [top, character] of characters.entries()) {
    assert.deepEqual(normalizeMatch({ ok: true, top, characters }), {
      kind: "A", characterId: character.id, image: character.image,
    });
  }
  for (const id of ["char_00", "char_09", "char_10", "char_11", "char_12", "char_13", "char_99", "../char_01", 1, null]) {
    assert.throws(() => normalizeMatch({ ok: true, top: 0, characters: [{ id }] }), {
      code: "INVALID_RESPONSE",
    });
  }
  const html = renderScreen({ screen: "detailA", aiMode: "A" }, false);
  assert.match(html, /8명의 MIRRORTING 캐릭터/);
  assert.doesNotMatch(html, /<details|<summary|class="how-list"/);
  for (const { thumbnail } of characters) assert.ok(html.includes(`src="${thumbnail}"`));
});
test("Mode B profile responses are normalized without accepting arbitrary image paths", () => {
  const profileId = `p_${"a".repeat(24)}`;
  assert.deepEqual(
    normalizeProfile({
      ok: true,
      profileId,
      previewUrl: `/api/profile/${profileId}/image`,
    }),
    {
      kind: "B",
      profileId,
      image: `/api/profile/${profileId}/image`,
    },
  );
  assert.throws(() => normalizeProfile({ ok: false, error: "no_face" }), {
    code: "NO_PERSON",
  });
  assert.throws(
    () => normalizeProfile({ ok: false, error: "multiple_faces" }),
    { code: "MULTIPLE_PEOPLE" },
  );
  assert.throws(
    () => normalizeProfile({ ok: false, error: "bad_position" }),
    { code: "BAD_POSITION" },
  );
  assert.throws(
    () => normalizeProfile({ ok: false, error: "profile_unavailable" }),
    { code: "INTEGRATION_PENDING", retryable: false },
  );
  assert.throws(
    () =>
      normalizeProfile({
        ok: true,
        profileId,
        previewUrl: "https://example.com/profile.png",
      }),
    { code: "INVALID_RESPONSE", retryable: false },
  );
});
test("Mode B posts the frame and operation ID, then deletes the temporary profile on reset", async () => {
  const calls = [];
  const profileId = `p_${"b".repeat(24)}`;
  const fetcher = async (path, options) => {
    calls.push({ path, options });
    return {
      ok: true,
      json: async () => ({
        ok: true,
        profileId,
        previewUrl: `/api/profile/${profileId}/image`,
      }),
    };
  };
  const api = createLiveApi({}, fetcher);
  const frame = new Blob(["capture"], { type: "image/jpeg" });
  const result = await api.generateProfile(frame, { operationId: "ai-job-1" });
  assert.equal(result.kind, "B");
  assert.equal(calls[0].path, "/api/profile/generate");
  assert.equal(calls[0].options.method, "POST");
  assert.equal(calls[0].options.body.get("operationId"), "ai-job-1");
  assert.equal(calls[0].options.body.get("frame").size, frame.size);
  api.reset();
  assert.equal(calls[1].path, `/api/profile/${profileId}`);
  assert.equal(calls[1].options.method, "DELETE");
});
test("Mode B keeps backend photo quality errors retryable", async () => {
  const api = createLiveApi({}, async () => ({
    ok: false,
    status: 422,
    json: async () => ({ ok: false, error: { code: "PROFILE_QUALITY_FAILED", retryable: true } }),
  }));
  await assert.rejects(
    api.generateProfile(new Blob(["synthetic"]), { operationId: "profile-attempt-1" }),
    { code: "PROFILE_QUALITY_FAILED", retryable: true },
  );
});
test("Result images must stay on the kiosk HTTP origin", () => {
  const base = "https://kiosk.local/checkin";
  assert.equal(
    isSameOriginImage("/api/profile/p_123/image", base),
    true,
  );
  assert.equal(isSameOriginImage("https://evil.example/photo", base), false);
  assert.equal(isSameOriginImage("javascript:alert(1)", base), false);
  assert.equal(isSameOriginImage("data:image/png;base64,AAAA", base), false);
});
test("Unimplemented NFC and printers do not call guessed routes", async () => {
  let calls = 0;
  const api = createLiveApi({}, async () => {
    calls++;
  });
  for (const method of [
    "registerNfc",
    "issueBadge",
    "resolveCheckout",
    "getMirrorTingReport",
    "printReport",
  ]) {
    await assert.rejects(api[method](), {
      code: "INTEGRATION_PENDING",
      retryable: false,
    });
  }
  assert.equal(calls, 0);
});
test("An ambiguous hardware failure cannot be retried blindly", async () => {
  const api = createLiveApi({
    issueBadge: async () => {
      throw new TypeError("network dropped after print");
    },
  });
  await assert.rejects(api.issueBadge("session"), {
    code: "UNKNOWN_OUTCOME",
    retryable: false,
  });
  const html = renderScreen(
    { screen: "badge", error: { code: "UNKNOWN_OUTCOME", retryable: false } },
    false,
  );
  assert.doesNotMatch(html, /data-action="(home|print-retry)"/);
  assert.match(html, /현장 스태프/);
});
test("Request timeout is bounded and external cancellation remains cancellation", async () => {
  const stalled = (_, { signal }) =>
    new Promise((_, reject) => {
      if (signal.aborted) reject(new DOMException("Aborted", "AbortError"));
      else
        signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        );
    });
  await assert.rejects(request("/api/match", { timeout: 5 }, stalled), {
    code: "AI_TIMEOUT",
  });
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(
    request("/api/match", { signal: controller.signal }, stalled),
    { name: "AbortError" },
  );
});
test("Explicit demo uses fixed results and supports an AI failure then a retry", async () => {
  const api = createDemoApi("ai_error");
  const ctx = { operationId: "ai-1" };
  await assert.rejects(api.matchCharacter(null, ctx), { code: "AI_ERROR" });
  const result = await api.matchCharacter(null, ctx);
  assert.equal(result.characterId, "char_01");
  assert.deepEqual(await api.matchCharacter(null, ctx), result);
});
test("Mode B demo keeps the camera and result identity consistent", async () => {
  const api = createDemoApi("success");
  const result = await api.generateProfile(null, { operationId: "profile-1" });
  const cameraHtml = renderScreen({ screen: "camera" }, true);
  assert.ok(cameraHtml.includes(`src="${characters[0].image}"`));
  assert.deepEqual(result, {
    kind: "B",
    image: characters[0].image,
    sample: true,
  });
});
test("Demo hardware retry keeps operation identity and badge/report intents distinct", async () => {
  const api = createDemoApi("printer_error");
  const ctx = { operationId: "print-1" };
  await assert.rejects(api.issueBadge("s", ctx), { code: "PRINTER_ERROR" });
  assert.equal((await api.issueBadge("s", ctx)).status, "success");
  assert.equal((await api.issueBadge("s", ctx)).status, "success");
  await assert.rejects(api.printReport({}, { operationId: "report-1" }), {
    code: "PRINTER_ERROR",
  });
});
test("Missing MirrorTing data stays missing instead of becoming a report", async () => {
  const api = createDemoApi("no_report");
  assert.deepEqual(await api.getMirrorTingReport("s", { operationId: "r" }), {
    status: "not_found",
  });
});


test("Live adapters preserve backend operation IDs and report identity", async () => {
  const calls = [];
  const fetcher = async (path, options) => {
    calls.push({ path, options });
    return { ok: true, json: async () => path.includes("/reports/") && options.method !== "POST"
      ? { ok: true, status: "available", sessionId: "MW2609300001", reportId: "42", mirrorSessionId: 42, source: "mirrorting" }
      : { ok: true, status: "preview", previewUrl: "/api/print/previews/test" } };
  };
  const integrations = createLiveIntegrations(fetcher);
  await integrations.registerNfc({ name: "김민수", teamId: "ai", aiMode: "B", result: { kind: "B", profileId: "p_test" } }, { operationId: "nfc-op" });
  await integrations.issueBadge("MW2609300001", { operationId: "badge-op" });
  await integrations.getMirrorTingReport("MW2609300001", {});
  await integrations.printReport({ sessionId: "MW2609300001", reportId: "42" }, { operationId: "report-op" });
  assert.equal(calls[0].path, "/api/nfc/register");
  assert.deepEqual(JSON.parse(calls[0].options.body).result, { kind: "B", profileId: "p_test" });
  assert.equal(JSON.parse(calls[1].options.body).operationId, "badge-op");
  assert.equal(calls[2].path, "/api/reports/MW2609300001");
  assert.deepEqual(JSON.parse(calls[3].options.body), { operationId: "report-op", sessionId: "MW2609300001", reportId: "42" });
});

test("Ambiguous write failures stay locked; report reads remain retryable", async () => {
  const integrations = createLiveIntegrations(async () => { throw new TypeError("connection lost"); });
  await assert.rejects(integrations.issueBadge("MW2609300001", { operationId: "badge-op" }), { code: "UNKNOWN_OUTCOME", retryable: false });
  await assert.rejects(integrations.getMirrorTingReport("MW2609300001", {}), { code: "BACKEND_UNAVAILABLE", retryable: true });
  const html = renderScreen({ screen: "badge", error: { code: "UNKNOWN_OUTCOME", retryable: false } }, false);
  assert.match(html, /data-action="operation-check"/);
  assert.doesNotMatch(html, /data-action="print-retry"/);
});

test("Print result wording distinguishes preview, sent command, and operator confirmation", () => {
  const base = { screen: "checkinComplete", name: "김민수", printResult: { status: "preview", previewUrl: "/api/print/previews/a" } };
  const preview = renderScreen(base, false);
  assert.match(preview, /실물 프린터로는 출력하지 않았어요/);
  assert.match(preview, /api\/print\/previews\/a/);
  const submitted = renderScreen({ ...base, printResult: { status: "submitted" } }, false);
  assert.match(submitted, /출력 명령을 보냈어요/);
  assert.doesNotMatch(submitted, /실물 출력을 확인했어요/);
  const confirmed = renderScreen({ ...base, printResult: { status: "confirmed" } }, false);
  assert.match(confirmed, /현장 스태프가 종이 출력 결과를 확인했어요/);
});

test("Sample completion gives a truthful next step and checkout photos remain optional", () => {
  for (const screen of ["checkinComplete", "checkoutComplete"]) {
    const html = renderScreen({ screen, name: "점검자", printResult: { status: "success" } }, true);
    assert.match(html, /실물 카드 등록과 출력은 없었어요/);
    assert.match(html, /카드 등록과 스마트미러 체험은 현장 스태프의 안내/);
    assert.doesNotMatch(html, /등록한 카드를 가지고|실물 인쇄 여부를 확인/);
    assert.equal((html.match(/화면 체험을 마쳤어요/g) || []).length, 1);
  }
  const base = { screen: "checkoutResult", name: "점검자", team: { title: "AI팀" } };
  const available = renderScreen({ ...base, report: { status: "available" } }, true);
  assert.match(available, /data-action="report-open"/);
  assert.match(available, /data-action="photo-skip"/);
  assert.match(available, /사진 없이 리포트 보기/);
  const missing = renderScreen({ ...base, report: { status: "not_found" } }, true);
  assert.doesNotMatch(missing, /data-action="photo-skip"|data-action="report-open"/);
});

test("Health checks always request fresh server state", async () => {
  const calls = [];
  const api = createLiveApi({}, async (path, options) => {
    calls.push({ path, options });
    return { ok: true, json: async () => ({ ok: true }) };
  });
  await api.getHealth();
  await api.getHealth();
  assert.equal(calls.length, 2);
  assert.ok(calls.every(({ path, options }) => path === "/api/health" && options.cache === "no-store"));
});

test("Live report renders source fields without inventing a scenario", () => {
  const report = {
    status: "available", source: "mirrorting", sessionId: "MW2609300001", reportId: "42", mirrorSessionId: 42,
    grade: "B", totalScore: 78,
    headline: { sentence: "차분한 <대화>", context: "상대방의 말을 들었어요." },
    fitScores: { voice: { label: "안정", summary: "목소리가 안정적이에요.", observation: true, provisional: false } },
    strengths: ["경청"], improvements: ["열린 질문"], coaching: [{ issue: "시선", suggestion: "상대방을 바라보세요." }],
    dayEnding: { label: "하루의 마무리", text: "오늘도 수고했어요." },
  };
  const html = renderScreen({ screen: "report", name: "김민수", team: { title: "AI팀" }, sessionId: "MW2609300001", report }, false);
  assert.match(html, /MirrorTing 세션 42/);
  assert.match(html, /차분한 &lt;대화&gt;/);
  assert.match(html, /목소리가 안정적이에요/);
  assert.match(html, /관찰 기록이 포함돼요/);
  assert.doesNotMatch(html, />true<|오늘의 시나리오|새로운 팀원과 첫 미팅/);
});

test("A profile attached to a backend session is not deleted by visitor reset", async () => {
  const calls = [];
  const profileId = `p_${"c".repeat(24)}`;
  const api = createLiveApi({}, async (path, options) => {
    calls.push({ path, options });
    return { ok: true, json: async () => ({ ok: true, profileId, previewUrl: `/api/profile/${profileId}/image` }) };
  });
  await api.generateProfile(new Blob(["photo"]), { operationId: "profile-op" });
  api.retainProfile(profileId);
  api.reset();
  assert.equal(calls.length, 1);
});
test("A camera stream that arrives after leaving the screen is immediately stopped", async () => {
  const descriptor = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
  let deliver;
  let stopped = 0;
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: {
      getUserMedia: () =>
        new Promise((resolve) => {
          deliver = resolve;
        }),
    },
  });
  try {
    const camera = new Camera();
    const pending = camera.start({ srcObject: null }, {}, () => {});
    camera.stop();
    deliver({ getTracks: () => [{ stop: () => stopped++ }] });
    await pending;
    assert.equal(stopped, 1);
    assert.equal(camera.stream, null);
  } finally {
    if (descriptor)
      Object.defineProperty(navigator, "mediaDevices", descriptor);
    else delete navigator.mediaDevices;
  }
});

test("An unanswered camera permission times out and a late stream is released", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const descriptor = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
  let deliver;
  let stopped = 0;
  const states = [];
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia: () => new Promise(resolve => { deliver = resolve; }) },
  });
  const camera = new Camera();
  try {
    const pending = camera.start({ srcObject: null }, {}, (...status) => states.push(status));
    t.mock.timers.tick(15000);
    assert.deepEqual(states.at(-1), ["error", "CAMERA_UNAVAILABLE"]);
    deliver({ getTracks: () => [{ stop: () => stopped++ }] });
    await pending;
    assert.equal(stopped, 1);
    assert.equal(camera.stream, null);
  } finally {
    camera.stop();
    if (descriptor) Object.defineProperty(navigator, "mediaDevices", descriptor);
    else delete navigator.mediaDevices;
  }
});

test("Camera loss stops capture, releases resources, and rejects late frames and detection", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const media = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
  const dom = Object.getOwnPropertyDescriptor(globalThis, "document");
  let stream, encode = (done) => done(new Blob(["frame"], { type: "image/jpeg" }));
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true, value: { getUserMedia: async () => stream },
  });
  Object.defineProperty(globalThis, "document", {
    configurable: true,
    value: { createElement: () => ({
      getContext: () => ({ drawImage() {} }),
      toBlob: (done) => encode(done),
    }) },
  });
  const camera = new Camera();
  t.after(() => {
    camera.stop();
    if (media) Object.defineProperty(navigator, "mediaDevices", media);
    else delete navigator.mediaDevices;
    if (dom) Object.defineProperty(globalThis, "document", dom);
    else delete globalThis.document;
  });
  for (const event of ["ended", "inactive", "backend_error"]) {
    const track = Object.assign(new EventTarget(), {
      readyState: "live", stops: 0,
      stop() { this.stops++; this.readyState = "ended"; },
    });
    stream = Object.assign(new EventTarget(), {
      active: true, getTracks: () => [track], getVideoTracks: () => [track],
    });
    const video = { srcObject: null, videoWidth: 1280, videoHeight: 960, play: async () => {} };
    const states = [];
    let calls = 0, deliver, rejectDetection, signal, started;
    const detecting = new Promise(resolve => { started = resolve; });
    await camera.start(video, {
      detectPreview: async (_, context) => {
        if (++calls === 1) return { ok: true, count: 1 };
        signal = context.signal;
        started();
        return new Promise((resolve, reject) => { deliver = resolve; rejectDetection = reject; });
      },
    }, (...status) => states.push(status));
    assert.deepEqual(states.at(-1), ["ready"]);
    t.mock.timers.tick(650);
    await detecting;
    if (event === "backend_error") rejectDetection(new KioskError("BACKEND_UNAVAILABLE"));
    else {
      track.readyState = "ended";
      stream.active = false;
      (event === "ended" ? track : stream).dispatchEvent(new Event(event));
      deliver({ ok: true, count: 1 });
    }
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(states.at(-1), ["error", event === "backend_error" ? "BACKEND_UNAVAILABLE" : "CAMERA_UNAVAILABLE"]);
    assert.equal(camera.stream, null);
    assert.equal(video.srcObject, null);
    assert.equal(track.stops, 1);
    assert.equal(signal.aborted, true);
    await assert.rejects(camera.capture(), { code: "CAMERA_UNAVAILABLE" });
  }
  // An image still encoding when the visitor leaves cannot become a new photo.
  const track = { readyState: "live", stop() {} };
  camera.stream = { active: true, getVideoTracks: () => [track], getTracks: () => [track] };
  camera.video = { videoWidth: 1280, videoHeight: 960, srcObject: null };
  let deliverImage;
  encode = (done) => { deliverImage = done; };
  const pending = camera.capture();
  camera.stop();
  deliverImage(new Blob(["old visitor frame"]));
  await assert.rejects(pending, { code: "CAMERA_UNAVAILABLE" });
});

test("Unknown badge and report outcomes expose the failed operation ID without unlocking print", () => {
  for (const screen of ["badge", "reportPrint"]) {
    const operationId = screen === "badge"
      ? "a0123456-7890-4abc-8123-456789abcdef"
      : "b0123456-7890-4abc-8123-456789abcdef";
    for (const reconciling of [false, true]) {
      const html = renderScreen({ screen, reconciling, error: { code: "UNKNOWN_OUTCOME", operationId, retryable: false } }, false);
      assert.match(html, /운영 확인용 작업 ID/);
      assert.ok(html.includes(`<code>${operationId}</code>`));
      assert.match(html, /data-action="operation-check"/);
      assert.doesNotMatch(html, /data-action="(home|print-retry)"/);
      if (reconciling) assert.match(html, /data-action="operation-check" disabled aria-busy="true"/);
    }
  }
});

test("Recovery IDs are escaped and disappear when the error or visitor is cleared", () => {
  const state = createState();
  state.patch({ screen: "badge", error: { code: "UNKNOWN_OUTCOME", operationId: '<img src=x onerror="alert(1)">', retryable: false } });
  const unknown = renderScreen(state.data, false);
  assert.match(unknown, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt;/);
  assert.doesNotMatch(unknown, /<img src=x/);
  state.patch({ error: { code: "PRINTER_ERROR", operationId: "old-operation", retryable: true } });
  assert.doesNotMatch(renderScreen(state.data, false), /운영 확인용 작업 ID|old-operation/);
  state.reset();
  assert.doesNotMatch(renderScreen(state.data, false), /운영 확인용 작업 ID|onerror/);
});
