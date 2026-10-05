import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { renderScreen } from "../../frontend/js/views.js";

test("Merged glass icons retain current entry labels and hardware error recovery", () => {
  const home = renderScreen({ screen: "home" }, false);
  assert.match(home, /입사하신 것을/);
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
