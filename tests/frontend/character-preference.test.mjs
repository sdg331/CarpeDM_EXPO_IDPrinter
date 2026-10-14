import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { characters, characterGenderOptions } from "../../frontend/js/content.js";
import { createState } from "../../frontend/js/state.js";
import { createLiveApi, createDemoApi } from "../../frontend/js/api-client.js";
import { renderScreen } from "../../frontend/js/views.js";

test("Character preference changes only before capture and resets for the next visitor", () => {
  const state = createState();
  assert.equal(state.data.characterGender, "any");
  const source = readFileSync(new URL("../../frontend/js/app.js", import.meta.url), "utf8");
  const context = { state, characterGenderOptions, render() {}, screen: { querySelector: () => ({ focus() {} }) } };
  runInNewContext(source.slice(source.indexOf("function chooseCharacterGender("), source.indexOf("function chooseCharacter(")), context);
  context.chooseCharacterGender("male");
  assert.equal(state.data.characterGender, "any");
  state.patch({ screen: "detailA" });
  context.chooseCharacterGender("male");
  assert.equal(state.data.characterGender, "male");
  context.chooseCharacterGender("unknown");
  assert.equal(state.data.characterGender, "male");
  state.patch({ busy: true });
  context.chooseCharacterGender("female");
  assert.equal(state.data.characterGender, "male");
  state.patch({ screen: "camera", busy: false });
  assert.equal(state.data.characterGender, "male");
  state.reset();
  assert.equal(state.data.characterGender, "any");
});

test("Catalogue configuration agrees with backend and renders only eligible portraits", () => {
  const genders = JSON.parse(readFileSync(new URL("../../assets/characters/genders.json", import.meta.url), "utf8"));
  assert.deepEqual(Object.fromEntries(characters.map(({ id, gender }) => [id, gender])), genders);
  for (const [gender] of characterGenderOptions) {
    const html = renderScreen({ screen: "detailA", aiMode: "A", characterGender: gender });
    assert.equal((html.match(/data-action="character-gender"/g) || []).length, 3);
    assert.match(html, new RegExp(`data-gender="${gender}" aria-pressed="true"`));
    for (const character of characters)
      assert.equal(html.includes(character.thumbnail), gender === "any" || character.gender === gender);
  }
});

test("Live recommendation transmits each preference with the captured frame", async () => {
  for (const gender of ["any", "male", "female"]) {
    let submitted;
    const api = createLiveApi({}, async (_, options) => {
      submitted = options.body;
      return { ok: true, json: async () => ({ ok: true, top: 0, characters: [{ id: "char_01" }] }) };
    });
    await api.matchCharacter(new Blob(["frame"]), { characterGender: gender });
    assert.equal(submitted.get("character_gender"), gender);
    assert.equal(await submitted.get("frame").text(), "frame");
  }
});

test("Sample recommendations honour the selected catalogue without random results", async () => {
  const api = createDemoApi();
  for (const gender of ["any", "male", "female"]) {
    const result = await api.matchCharacter(null, { characterGender: gender, operationId: gender });
    const character = characters.find(({ id }) => id === result.characterId);
    assert.ok(character);
    assert.ok(gender === "any" || character.gender === gender);
  }
});
