import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { renderScreen } from "../../frontend/js/views.js";

test("Card artwork stops its working motion when an error is shown", () => {
  const state = { name: "김미래", team: { title: "개발팀" }, busy: true, nfc: "writing" };
  for (const screen of ["nfc", "checkout"]) {
    assert.match(renderScreen({ ...state, screen }, false), /status-art working/);
    const error = renderScreen({ ...state, screen, error: { code: "NFC_ERROR", retryable: true } }, false);
    assert.doesNotMatch(error, /status-art working/);
    assert.match(error, /role="alert"/);
    assert.match(error, /다시 시도하기/);
  }
});

test("Merged glass icons retain current entry labels and hardware error recovery", () => {
  const home = renderScreen({ screen: "home" }, false);
  assert.match(home, /입사를 진심으로<br>축하합니다\./);
  assert.match(home, /aria-label="출근하기"/);
  const screens = [[home, ["checkin-badge", "checkout-report"]]];
  const state = { name: "김미래", team: { title: "디자인팀" }, aiMode: "A" };
  for (const screen of ["nfc", "checkout", "badge", "reportPrint"]) {
    const html = renderScreen({ ...state, screen, error: { code: "BACKEND_UNAVAILABLE", retryable: true } }, false);
    screens.push([html, [screen === "nfc" || screen === "checkout" ? "nfc-register" : "thermal-printer"]]);
    assert.match(html, /role="alert"/);
    assert.match(html, /data-action="(?:nfc-write|checkout-read|print-retry)"/);
    assert.doesNotMatch(html, /실물 출력을 확인했어요/);
  }
  for (const screen of ["checkinComplete", "checkoutComplete"]) {
    screens.push([renderScreen({ ...state, screen }, true), ["completion-check"]]);
  }
  const report = renderScreen({ screen: "webReport" }, false, true);
  screens.push([report, ["checkout-report"]]);
  screens.push([renderScreen({ screen: "webCheckout" }, false, true), ["nfc-register"]]);
  assert.match(report, /아직 연결된 체험 기록이 없어요/);
  assert.doesNotMatch(report, /data-action="report-print"/);
  for (const [html, names] of screens) {
    for (const name of names) {
      assert.ok(html.includes(`src="/assets/kiosk-icons/${name}.png" alt="" aria-hidden="true"`));
      const png = readFileSync(new URL(`../../assets/kiosk-icons/${name}.png`, import.meta.url));
      assert.equal(png.subarray(1, 4).toString(), "PNG");
      assert.equal(png[25], 6, "Artwork must retain RGBA transparency");
    }
  }
});
