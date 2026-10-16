import test from "node:test";
import assert from "node:assert/strict";
import { createLiveApi, normalizeMatch } from "../../frontend/js/api-client.js";
import { createLiveIntegrations } from "../../frontend/js/live-integrations.js";
import { characters, matchingCharacters } from "../../frontend/js/content.js";
import { renderScreen } from "../../frontend/js/views.js";

const keys = ["face_aspect", "jaw_width", "eye_spacing", "eye_width", "eye_aspect", "nose_width", "nose_length", "mouth_width", "lower_face"];
function response(gender = "any") {
  const character = matchingCharacters(gender)[0];
  return { ok: true, engine: "mediapipe_ratios", top: characters.indexOf(character), characters,
    characterGender: gender, externalUpload: false,
    face: { count: 1, selection: "largest_visible_face", source: "mediapipe", imageSize: [640, 480],
      box: [.2, .1, .5, .8], landmarks: Array.from({ length: 478 }, () => [.5, .5]) },
    analysis: { engine: "mediapipe_ratios", characterId: character.id, candidateCount: matchingCharacters(gender).length,
      featureCount: 9, distributionCorrected: true, likenessValidated: false,
      comparisons: keys.map((key, i) => ({ key, measuredRatio: .4 + i / 100,
        characterRatio: .5 + i / 100, comparisonDifference: .1 + i / 10 })) } };
}

test("Live visitor matching calls MediaPipe and keeps its measured explanation", async () => {
  for (const gender of ["any", "male", "female"]) {
    const data = response(gender);
    let face, path;
    const api = createLiveApi({}, async (url, options) => {
      path = url;
      assert.equal(options.body.get("character_gender"), gender);
      return { ok: true, json: async () => data };
    });
    const result = await api.matchCharacter(new Blob(["frame"]), { characterGender: gender, onFace: value => { face = value; } });
    assert.equal(path, "/api/match/landmarks");
    assert.equal(result.characterId, data.analysis.characterId);
    assert.equal(result.analysis.comparisons[0].label, "얼굴 길이");
    assert.equal(face.landmarks.length, 478);
  }
});

test("Mismatched candidates and fabricated or missing measurements are rejected", async () => {
  for (const alter of [
    data => { data.analysis.characterId = "char_08"; },
    data => { data.analysis.comparisons[0].measuredRatio = NaN; },
    data => { data.analysis.comparisons[0].key = "__proto__"; },
    data => { data.analysis.comparisons[0].key = data.analysis.comparisons[1].key; },
  ]) {
    const data = response(); alter(data);
    assert.throws(() => normalizeMatch(data), { code: "INVALID_RESPONSE" });
  }
  const data = response("female"); data.top = 1;
  const api = createLiveApi({}, async () => ({ ok: true, json: async () => data }));
  await assert.rejects(api.matchCharacter(new Blob(["frame"]), { characterGender: "female" }), { code: "INVALID_RESPONSE" });
});

test("Both result layouts explain measured ratios and hide them after manual selection", () => {
  const result = normalizeMatch(response());
  const state = { screen: "resultA", aiMode: "A", result, name: "김미래", team: { title: "디자인팀" } };
  for (const web of [false, true]) {
    const html = renderScreen(state, false, web);
    assert.match(html, /이렇게 추천했어요/);
    assert.match(html, /8명의 캐릭터와 9개 비율/);
    assert.match(html, /0\.400/);
    assert.match(html, /보정 전 측정 비율/);
    assert.doesNotMatch(html, /닮음 \d+%|comparisonDifference/);
    assert.doesNotMatch(renderScreen({ ...state, characterChosen: true }, false, web), /match-reason/);
    assert.doesNotMatch(renderScreen({ ...state, result: { ...result, analysis: null } }, true, web), /match-reason/);
  }
});

test("Measured face ratios never enter NFC registration payloads", async () => {
  const result = normalizeMatch(response());
  let submitted;
  const api = createLiveIntegrations(async (_, options) => {
    submitted = JSON.parse(options.body);
    return { ok: true, json: async () => ({ ok: true, status: "verified", sessionId: "test" }) };
  });
  await api.registerNfc({ name: "김미래", teamId: "design", aiMode: "A", result }, { operationId: "measured-result-test" });
  assert.deepEqual(submitted.result, { kind: "A", characterId: result.characterId });
});
