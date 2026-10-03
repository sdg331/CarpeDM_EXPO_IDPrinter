import { isSameOriginImage, KioskError } from "./api-client.js";
import { validateName } from "./state.js";

// Produces a real PNG in browser memory; it never sends a print or NFC command.
export async function createDigitalBadge({ name, team, result }, { signal } = {}) {
  if (!validateName(name).valid || !team?.title || !isSameOriginImage(result?.image, location.href))
    throw new KioskError("INVALID_RESPONSE", false);
  const response = await fetch(result.image, { signal, cache: "no-store" });
  if (!response.ok) throw new KioskError("PROFILE_EXPIRED");
  const photo = await createImageBitmap(await response.blob());
  const canvas = document.createElement("canvas");
  canvas.width = 900;
  canvas.height = 1200;
  const ctx = canvas.getContext("2d");
  try {
    await document.fonts.ready;
    signal?.throwIfAborted();
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, 900, 1200);
    ctx.fillStyle = "#1b64da";
    ctx.fillRect(0, 0, 900, 155);
    ctx.fillStyle = "#ffffff";
    ctx.font = '700 42px "Pretendard Variable", sans-serif';
    ctx.fillText("MIRRORTING WORKS", 64, 95);
    const width = 420, height = 560;
    const scale = Math.min(width / photo.width, height / photo.height);
    ctx.fillStyle = "#f2f4f6";
    ctx.fillRect(240, 205, width, height);
    ctx.drawImage(photo, 240 + (width - photo.width * scale) / 2,
      205 + (height - photo.height * scale) / 2, photo.width * scale, photo.height * scale);
    ctx.textAlign = "center";
    ctx.fillStyle = "#191f28";
    let size = 68;
    do { ctx.font = `700 ${size--}px "Pretendard Variable", sans-serif`; }
    while (ctx.measureText(name).width > 740 && size > 30);
    ctx.fillText(name, 450, 867);
    ctx.fillStyle = "#6b7684";
    ctx.font = '500 36px "Pretendard Variable", sans-serif';
    ctx.fillText(team.title, 450, 927);
    ctx.fillStyle = "#e5e8eb";
    ctx.fillRect(64, 985, 772, 2);
    ctx.font = '500 25px "Pretendard Variable", sans-serif';
    ctx.fillStyle = "#6b7684";
    ctx.fillText("2026 EXPO · MIRRORTING 사원증", 450, 1050);
    ctx.font = '400 23px "Pretendard Variable", sans-serif';
    ctx.fillText("CarpeDM × 동양미래대학교", 450, 1100);
    ctx.fillText("출력 미리보기 · 실물 카드 등록 전", 450, 1148);
    return await new Promise((resolve, reject) => canvas.toBlob(blob => {
      if (signal?.aborted) reject(new DOMException("Aborted", "AbortError"));
      else if (blob) resolve(blob);
      else reject(new KioskError("DOWNLOAD_FAILED"));
    }, "image/png"));
  } finally {
    photo.close();
    canvas.width = canvas.height = 0;
  }
}
