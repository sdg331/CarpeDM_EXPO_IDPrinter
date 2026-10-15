import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { renderScreen, renderPrintRecovery } from "../../frontend/js/views.js";
import { createLiveApi, createDemoApi } from "../../frontend/js/api-client.js";
import { createLiveIntegrations } from "../../frontend/js/live-integrations.js";
import { createState } from "../../frontend/js/state.js";

const app = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");

test("Print errors offer batch recovery while uncertain NFC writes stay separate", () => {
  for (const screen of ["badge", "reportPrint"])
    for (const code of ["UNKNOWN_OUTCOME", "PRINTER_ERROR", "PRINT_UNAVAILABLE"])
      assert.match(renderScreen({ screen, flow: "checkin", error: { code, retryable: code !== "UNKNOWN_OUTCOME" } }, false), /data-action="print-recovery-open"/);
  assert.match(renderScreen({ screen: "checkout", flow: "souvenir", error: { code: "SOUVENIR_PRINT_PENDING" } }, false), /data-action="print-recovery-open"/);
  assert.doesNotMatch(renderScreen({ screen: "nfc", error: { code: "UNKNOWN_OUTCOME" } }, false), /data-action="print-recovery-open"/);
});

test("Recovery dialog requires selection and explains legacy, busy and completed outcomes", () => {
  const html = renderPrintRecovery({ pending: [
    { operationId: '<unsafe>', kind: "souvenir_print", status: "unknown", recoverable: true, hasImage: true },
    { operationId: "old-photo", kind: "souvenir_print", status: "unknown", recoverable: true, hasImage: false },
    { operationId: "busy-photo", kind: "souvenir_print", status: "running", recoverable: false, hasImage: true },
  ] });
  assert.match(html, /aria-modal="true"/);
  assert.match(html, /value="&lt;unsafe&gt;"/);
  assert.doesNotMatch(html, /<unsafe>/);
  assert.match(html, /이전 이미지 없음/);
  assert.match(html, /value="busy-photo" disabled/);
  assert.match(html, /data-action="print-recovery-submit" disabled/);
  assert.match(html, /선택한 건 이미 출력됨/);
  const result = renderPrintRecovery({ operationIds: ["a", "b", "c", "d"], results: [
    { operationId: "a", status: "submitted" }, { operationId: "b", status: "missing_image" }, { operationId: "c", status: "unknown" },
  ] });
  assert.match(result, /1건 전송/);
  assert.match(result, /차단만 해제/);
  assert.match(result, /남은 1건은 대기/);
  assert.doesNotMatch(result, /출력 완료/);
});

test("Both photo previews show the exact encouragement before the large CarpeDM stamp", () => {
  for (const screen of ["photoReview", "report"]) {
    const html = renderScreen({ screen, flow: "souvenir", souvenirPhoto: "blob:photo", report: {} }, true);
    assert.match(html, /오늘 하루도 고생 많으셨습니다/);
    assert.match(html, /저희의 처음에 함께해 주셔서 감사합니다/);
    assert.match(html, /ticket-stamp"><strong>CarpeDM<\/strong><span>오늘의 당신을 응원합니다/);
    assert.ok(html.indexOf('src="blob:photo"') < html.indexOf("오늘 하루도"));
    assert.ok(html.indexOf("오늘 하루도") < html.indexOf('class="ticket-stamp"'));
  }
});

test("Recovery POST uses a stable batch ID and explicit operator outcome", async () => {
  let payload, path;
  const api = createLiveApi(createLiveIntegrations(async (url, options) => {
    path = url; payload = JSON.parse(options.body);
    return { ok: true, json: async () => ({ ok: true, results: [] }) };
  }));
  await api.recoverPrints([{ operationId: "pending-print-001", revision: "original" }], "not_printed", { operationId: "fixed-batch-id" });
  assert.equal(path, "/api/print/recovery");
  assert.deepEqual(payload, { operationId: "fixed-batch-id", operationIds: ["pending-print-001"], outcome: "not_printed", confirmed: true, revisions: { "pending-print-001": "original" } });
});

test("Canonical print operation ID survives API wrapping after a browser refresh", async () => {
  const api = createLiveApi(createLiveIntegrations(async () => ({ ok: false, json: async () => ({
    ok: false, error: { code: "UNKNOWN_OUTCOME", retryable: false, operationId: "original-print-id" },
  }) })));
  await assert.rejects(api.issueBadge("session", { operationId: "new-browser-id" }), error => error.operationId === "original-print-id");
});

test("Late queue response after a visitor reset cannot reopen the recovery dialog", async () => {
  const state = createState(); state.patch({ screen: "badge", error: { code: "UNKNOWN_OUTCOME" } });
  let resolve, opened = 0;
  const context = { state, AbortController, currentController: null, printRecovery: null,
    render() {}, openModal() { opened++; }, api: { getPrintRecovery: () => new Promise(done => { resolve = done; }) } };
  runInNewContext(app.slice(app.indexOf("async function openPrintRecovery()"), app.indexOf("function recoverPrints(")), context);
  const pending = context.openPrintRecovery();
  state.reset(); resolve({ ok: true, pending: [] }); await pending;
  assert.equal(opened, 0); assert.equal(state.data.screen, "home");
});

test("Sample recovery remains a sample and never calls physical integration", async () => {
  const api = createDemoApi("printer_error");
  const listing = await api.getPrintRecovery();
  const result = await api.recoverPrints(listing.pending, "not_printed");
  assert.equal(result.results[0].status, "preview");
  assert.match(renderPrintRecovery(result, true), /샘플 화면 · 실물 출력 없음/);
});
