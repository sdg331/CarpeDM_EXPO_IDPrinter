import test from "node:test";
import assert from "node:assert/strict";
import { createState, validateName } from "../../frontend/js/state.js";
import {
  createLiveApi,
  createDemoApi,
  isSameOriginImage,
  normalizeMatch,
  normalizeProfile,
  request,
} from "../../frontend/js/api-client.js";
import { Camera } from "../../frontend/js/camera.js";
import { renderScreen, renderTeamPreview } from "../../frontend/js/views.js";
import { resolveRuntime } from "../../frontend/js/runtime.js";
import { applyTouchKey } from "../../frontend/js/hangul-keyboard.js";
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
  assert.match(issue, /ACR1252U 미연결/);
  assert.match(issue, /data-action="digital-card"/);
  assert.doesNotMatch(issue, /data-action="nfc-write"/);
  const card = renderScreen({ ...state, screen: 'webCard', digitalCard: 'blob:http://localhost/test' }, false, true);
  assert.match(card, /download="MIRRORTING-ID.png"/);
  assert.match(card, /실물 카드 등록이나 출력을 진행하지 않았어요/);
});

test("Kiosk home explains check-in, MirrorTing, and checkout; absent records remain empty", () => {
  const home = renderScreen({ screen: 'home' }, false, true);
  assert.match(home, /data-action="checkin"/);
  assert.match(home, /data-action="checkout"/);
  assert.match(home, /스마트미러/);
  assert.match(home, /입사하신 것을/);
  assert.match(home, /웹 미리보기에서는/);
  assert.match(home, /로컬 AI/);
  assert.match(home, /NFC/);
  assert.match(home, /출력/);
  const report = renderScreen({ screen: 'webReport' }, false, true);
  assert.match(report, /아직 연결된 체험 기록이 없어요/);
  assert.doesNotMatch(report, /data-action="report-print"/);
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

test("Browser hardware preview names the Raspberry Pi devices without claiming success", () => {
  const state = { name: '김미래', team: { title: '디자인팀' }, aiMode: 'B', result: { image: '/api/profile/p_test/image' } };
  const issue = renderScreen({ ...state, screen: 'webIssue' }, false, true);
  assert.match(issue, /Raspberry Pi 카드 등록/);
  assert.match(issue, /ACR1252U 미연결/);
  assert.doesNotMatch(issue, /등록 완료/);
  const card = renderScreen({ ...state, screen: 'webCard', digitalCard: 'blob:http:\/\/localhost\/test' }, false, true);
  assert.match(card, /ZTP-80USL2 미연결/);
  assert.match(card, /Raspberry Pi에서 출력될/);
  assert.doesNotMatch(card, /출력 완료/);
});

test("Camera screen auto-starts without a separate permission button", () => {
  const camera = renderScreen({ screen: "camera", aiMode: "B" }, false, true);
  assert.match(camera, /data-action="capture"/);
  assert.match(camera, /카메라 권한과 연결을 확인하고 있어요/);
  assert.doesNotMatch(camera, /data-action="camera-start"|카메라 켜기|카메라 허용/);
  assert.match(camera, /camera-facemap/);
  assert.match(camera, /aria-hidden="true"/);
  assert.doesNotMatch(camera, /photo-upload|type="file"|사진 파일로 시작하기/);
});

test("AI mode selection uses the supplied cover artwork for both options", () => {
  const screen = renderScreen({ screen: "modes", name: "김미래" }, false, true);
  assert.match(screen, /ai-mode-a-cover\.jpg/);
  assert.match(screen, /ai-mode-b-cover\.jpg/);
  assert.match(screen, /width="720" height="720"/);
  assert.doesNotMatch(screen, /profile-icon|characters\/char_0[13]\.png/);
});

test("AI processing uses an indeterminate visual without invented progress stages", () => {
  const modeA = renderScreen({ screen: "processing", aiMode: "A" }, false, true);
  assert.match(modeA, /ai-facemap/);
  assert.match(modeA, /얼굴 특징을 읽고 캐릭터와 비교/);
  assert.doesNotMatch(modeA, /analysis-pipeline/);
  assert.doesNotMatch(modeA, /\d+%|정확도/);

  const modeB = renderScreen({ screen: "processing", aiMode: "B" }, false, true);
  assert.match(modeB, /얼굴 위치를 읽고 프로필 구도/);
  assert.doesNotMatch(modeB, /analysis-pipeline/);
  assert.doesNotMatch(modeB, /SFace|\d+%|정확도/);
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
test("Reset isolates all visitor data and rejects late responses", () => {
  const state = createState();
  state.patch({
    screen: "nfc",
    name: "이전사용자",
    team: { id: "ai" },
    draftTeam: {},
    aiMode: "B",
    capture: new Blob(["photo"]),
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
    image: "/assets/characters/char_01.png",
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
  assert.match(cameraHtml, /src="\/assets\/characters\/char_01\.png"/);
  assert.deepEqual(result, {
    kind: "B",
    image: "/assets/characters/char_01.png",
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

test("Touch keyboard composes Korean names and keeps physical text input available", () => {
  const type = (keys) => [...keys].reduce((value, key) => applyTouchKey(value, key), "");
  assert.equal(type("ㄱㅣㅁㅁㅣㄴㅅㅜ"), "김민수");
  assert.equal(type("ㅎㅏㄴㅏ"), "하나");
  assert.equal(type("ㅎㅘ"), "화");
  assert.equal(applyTouchKey("김민수", "backspace"), "김민ㅅ");
  const name = renderScreen({ screen: "name", name: "", team: { id: "ai", title: "AI팀", iconImage: "/assets/teams/ai.png" } }, false);
  assert.match(name, /data-action="touch-keyboard"/);
  assert.match(name, /id="visitor-name"/);
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
