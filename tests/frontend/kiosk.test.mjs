import test from "node:test";
import assert from "node:assert/strict";
import { createState, validateName } from "../../frontend/js/state.js";
import {
  createLiveApi,
  createDemoApi,
  normalizeMatch,
  request,
} from "../../frontend/js/api-client.js";
import { Camera } from "../../frontend/js/camera.js";
import { renderScreen } from "../../frontend/js/views.js";

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
test("Unimplemented NFC, Mode B and printers do not call guessed routes", async () => {
  let calls = 0;
  const api = createLiveApi({}, async () => {
    calls++;
  });
  for (const method of [
    "registerNfc",
    "generateProfile",
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
