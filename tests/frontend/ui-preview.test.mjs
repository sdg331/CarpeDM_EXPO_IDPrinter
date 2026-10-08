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
