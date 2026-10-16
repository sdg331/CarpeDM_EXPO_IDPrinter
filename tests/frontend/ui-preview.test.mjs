import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { previewScreens, previewState } from "../../frontend/js/ui-preview.js";
import { renderScreen, renderTeamPreview } from "../../frontend/js/views.js";
import { teams, screenIds } from "../../frontend/js/content.js";

test("Team selection advances to name input without SCR-03", () => {
  assert.ok(!previewScreens.some(([id]) => id === "team"));
  const source = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");
  const select = source.split('"team-select": (el) => {')[1].split('"team-confirm":')[0];
  assert.match(select, /if \(team\) go\("name", \{ team \}\)/);
  assert.doesNotMatch(select, /openModal/);
});

test("Every UI preview renders all teams and states with valid sample data", () => {
  for (const [id] of previewScreens) {
    for (const team of teams) {
      for (const variant of ["default", "loading", "error", "empty", "unknown"]) {
        const { state, web } = previewState(id, team.id, variant);
        assert.ok(screenIds[state.screen], id);
        assert.equal(state.team.id, team.id);
        const html = renderScreen(state, true, web);
        assert.match(html, /class="view"/);
        if (id !== "fatal") assert.doesNotMatch(html, /WE’LL BE RIGHT BACK/, id);
        assert.doesNotMatch(html, /src="(?:undefined|null)"/, id);
        if (id === "team") assert.match(renderTeamPreview(state.draftTeam), /role="dialog"/);
      }
    }
  }
  const fallback = previewState("<invalid>", "missing");
  assert.equal(fallback.state.screen, "home");
  assert.equal(fallback.state.team.id, teams[0].id);
});

test("Report loading hides stale report actions and summary", () => {
  const { state } = previewState("checkoutResult", "development", "loading");
  assert.equal(state.report.status, "available");
  const html = renderScreen(state, true, false);
  assert.match(html, /체험 기록을 불러오고 있어요/);
  assert.match(html, /data-action="report-fetch"[^>]*disabled/);
  assert.doesNotMatch(html, /data-action="(?:report-open|photo-skip)"/);
  assert.ok(!html.includes(state.report.summary));
});

test("Preview failures describe the operation on screen", () => {
  for (const [id, code] of [["checkoutResult", "REPORT_UNAVAILABLE"], ["webIssue", "DOWNLOAD_FAILED"]]) {
    const { state, web } = previewState(id, "development", "error");
    assert.equal(state.error.code, code);
    assert.doesNotMatch(renderScreen(state, true, web), /분석하지 못했어요|다시 촬영해주세요/);
  }
});

test("Report errors remain distinct from missing records and respect retryability", () => {
  const { state } = previewState("checkoutResult", "development");
  for (const retryable of [true, false]) {
    const html = renderScreen({ ...state, error: { code: "REPORT_UNAVAILABLE", retryable } }, true);
    assert.match(html, /체험 기록을<br>확인하지 못했어요/);
    assert.match(html, /role="alert"/);
    assert.match(html, /김미래/);
    assert.match(html, /data-action="home"/);
    assert.equal(/data-action="report-fetch"/.test(html), retryable);
    assert.doesNotMatch(html, /class="record-card"|아직 체험 기록을 찾지 못했어요|data-action="(?:report-open|photo-skip)"/);
    assert.ok(!html.includes(state.report.summary));
  }
  const { state: empty } = previewState("checkoutResult", "development", "empty");
  const html = renderScreen(empty, true);
  assert.match(html, /아직 체험 기록을 찾지 못했어요/);
  assert.match(html, /data-action="report-fetch"/);
  assert.doesNotMatch(html, /role="alert"/);
});
