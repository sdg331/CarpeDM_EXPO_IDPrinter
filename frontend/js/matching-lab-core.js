import { characters, matchingCharacters } from "./content.js?v=20261013-character-gender-r1";
import { validateFace } from "./face-overlay.js?v=20261014-face-map-r1";

export function validateComparison(data, gender) {
  const allowed = new Set(matchingCharacters(gender).map(c => c.id));
  if (!data?.ok || data.experimental !== true || data.externalUpload !== false || data.characterGender !== gender)
    throw new Error("INVALID_RESPONSE");
  if (data.ratios?.distributionCorrected !== true) throw new Error("INVALID_RESPONSE");
  if (!data.face) throw new Error("INVALID_RESPONSE");
  validateFace(data.face);
  for (const [result, key] of [[data.sface, "score"], [data.ratios, "distance"]]) {
    if (!allowed.has(result?.characterId) || !Array.isArray(result.ranking) || result.ranking.length !== allowed.size ||
        new Set(result.ranking.map(row => row.characterId)).size !== allowed.size ||
        result.ranking.some(row => !allowed.has(row.characterId) || !Number.isFinite(row[key])) ||
        result.ranking[0].characterId !== result.characterId || !Number.isFinite(result.elapsedMs) || result.elapsedMs < 0)
      throw new Error("INVALID_RESPONSE");
  }
  if (!Array.isArray(data.ratios.landmarks) || data.ratios.landmarks.length !== 478 ||
      data.ratios.landmarks.some(point => !Array.isArray(point) || point.length !== 2 || point.some(v=>!Number.isFinite(v) || Math.abs(v)>2)))
    throw new Error("INVALID_RESPONSE");
  return data;
}

export function recommendationMarkup(result) {
  const character = characters.find(c => c.id === result.characterId);
  if (!character) throw new Error("INVALID_RESPONSE");
  const ranked = result.ranking.slice(0,3).map(row => {
    const item = characters.find(c => c.id === row.characterId);
    if (!item) throw new Error("INVALID_RESPONSE");
    return `<img src="${item.thumbnail}" alt="후보 캐릭터 ${item.id.slice(-2)}">`;
  }).join("");
  return `<img class="result-photo" src="${character.image}" alt="추천 캐릭터 ${character.id.slice(-2)}"><p class="result-name">캐릭터 ${character.id.slice(-2)}</p><p>처리 시간 ${(result.elapsedMs/1000).toFixed(2)}초</p><div class="ranking" aria-label="가까운 후보 세 명">${ranked}</div>`;
}
