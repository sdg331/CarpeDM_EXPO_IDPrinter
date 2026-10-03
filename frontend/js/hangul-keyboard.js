// Small touch keyboard composer for the kiosk's Korean name field. The normal
// text input remains available for a physical keyboard and the OS IME.
const INITIAL = [..."ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"];
const MEDIAL = [..."ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"];
const FINAL = [..."_ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"];
const COMPLEX_VOWELS = {
  "ㅗㅏ": "ㅘ", "ㅗㅐ": "ㅙ", "ㅗㅣ": "ㅚ",
  "ㅜㅓ": "ㅝ", "ㅜㅔ": "ㅞ", "ㅜㅣ": "ㅟ", "ㅡㅣ": "ㅢ",
};
const SPLIT_VOWELS = Object.fromEntries(Object.entries(COMPLEX_VOWELS).map(([pair, value]) => [value, pair[0]]));
const COMPLEX_FINALS = {
  "ㄱㅅ": "ㄳ", "ㄴㅈ": "ㄵ", "ㄴㅎ": "ㄶ", "ㄹㄱ": "ㄺ",
  "ㄹㅁ": "ㄻ", "ㄹㅂ": "ㄼ", "ㄹㅅ": "ㄽ", "ㄹㅌ": "ㄾ",
  "ㄹㅍ": "ㄿ", "ㄹㅎ": "ㅀ", "ㅂㅅ": "ㅄ",
};
const SPLIT_FINALS = Object.fromEntries(Object.entries(COMPLEX_FINALS).map(([pair, value]) => [value, [...pair]]));

const syllable = (initial, medial, final = 0) =>
  String.fromCodePoint(0xac00 + (initial * 21 + medial) * 28 + final);

function decompose(char) {
  const code = char.codePointAt(0) - 0xac00;
  if (code < 0 || code >= 11172) return null;
  return {
    initial: Math.floor(code / 588),
    medial: Math.floor((code % 588) / 28),
    final: code % 28,
  };
}

export function applyTouchKey(value, key) {
  const chars = Array.from(String(value));
  if (key === "backspace") {
    const last = chars.pop();
    if (!last) return "";
    const parts = decompose(last);
    if (!parts) return chars.join("");
    if (parts.final) {
      const final = FINAL[parts.final];
      const simpler = SPLIT_FINALS[final]?.[0];
      return chars.join("") + syllable(parts.initial, parts.medial, simpler ? FINAL.indexOf(simpler) : 0);
    }
    const vowel = MEDIAL[parts.medial];
    if (SPLIT_VOWELS[vowel])
      return chars.join("") + syllable(parts.initial, MEDIAL.indexOf(SPLIT_VOWELS[vowel]));
    return chars.join("") + INITIAL[parts.initial];
  }
  if (key === "space") return chars.join("") + " ";
  if (typeof key !== "string" || Array.from(key).length !== 1) return chars.join("");
  const last = chars.pop();
  if (!last) return key;
  const parts = decompose(last);
  if (MEDIAL.includes(key)) {
    const initial = INITIAL.indexOf(last);
    if (initial >= 0) return chars.join("") + syllable(initial, MEDIAL.indexOf(key));
    if (parts) {
      if (parts.final) {
        const final = FINAL[parts.final];
        const split = SPLIT_FINALS[final];
        const remain = split?.[0];
        const next = split?.[1] || final;
        const nextInitial = INITIAL.indexOf(next);
        if (nextInitial >= 0) return chars.join("") + syllable(parts.initial, parts.medial, remain ? FINAL.indexOf(remain) : 0) + syllable(nextInitial, MEDIAL.indexOf(key));
      } else {
        const combined = COMPLEX_VOWELS[MEDIAL[parts.medial] + key];
        if (combined) return chars.join("") + syllable(parts.initial, MEDIAL.indexOf(combined));
      }
    }
    return chars.join("") + last + key;
  }
  if (INITIAL.includes(key)) {
    if (parts) {
      if (!parts.final && FINAL.includes(key))
        return chars.join("") + syllable(parts.initial, parts.medial, FINAL.indexOf(key));
      const combined = COMPLEX_FINALS[FINAL[parts.final] + key];
      if (parts.final && combined)
        return chars.join("") + syllable(parts.initial, parts.medial, FINAL.indexOf(combined));
    }
    return chars.join("") + last + key;
  }
  return chars.join("") + last + key;
}
