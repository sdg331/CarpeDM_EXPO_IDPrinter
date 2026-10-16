// All coordinates come from the selected face in the uploaded image.
export function validateFace(face) {
  if (!face) return null;
  if (!Number.isInteger(face.count) || face.count < 1 || face.selection !== "largest_visible_face" ||
      !["yunet", "mediapipe"].includes(face.source) || !Array.isArray(face.imageSize) ||
      face.imageSize.length !== 2 || face.imageSize.some(v => !Number.isFinite(v) || v < 16) ||
      !Array.isArray(face.box) || face.box.length !== 4 ||
      face.box.some(v => !Number.isFinite(v) || v < 0 || v > 1) || face.box[2] <= 0 || face.box[3] <= 0 ||
      !Array.isArray(face.landmarks) || face.landmarks.length !== (face.source === "yunet" ? 5 : 478) ||
      face.landmarks.some(p => !Array.isArray(p) || p.length !== 2 || p.some(v => !Number.isFinite(v) || Math.abs(v) > 2)))
    throw new Error("INVALID_FACE_COORDINATES");
  return face;
}

export function overlayTransform(imageWidth, imageHeight, width, height, fit = "contain", mirrored = false) {
  const scale = Math[fit === "cover" ? "max" : "min"](width / imageWidth, height / imageHeight);
  const drawWidth = imageWidth * scale, drawHeight = imageHeight * scale;
  const left = (width - drawWidth) / 2, top = (height - drawHeight) / 2;
  return ([x, y]) => [mirrored ? width - (left + x * drawWidth) : left + x * drawWidth, top + y * drawHeight];
}

const contours = [
  [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109,10],
  [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246,33],
  [263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466,263],
  [61,146,91,181,84,17,314,405,321,375,291,409,270,269,267,0,37,39,40,185,61],
  [168,6,197,195,5,4,1,2],
];

export function drawFaceOverlay(canvas, face, { fit = "contain", mirrored = false, visible = true, allPoints = false } = {}) {
  if (!canvas) return;
  try { validateFace(face); } catch { face = null; }
  canvas.hidden = !face || !visible;
  if (canvas.hidden) { canvas.width = canvas.height = 0; return; }
  const width = canvas.parentElement.clientWidth, height = canvas.parentElement.clientHeight;
  if (!width || !height) return;
  const ratio = globalThis.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio);
  const transform = overlayTransform(...face.imageSize, width, height, fit, mirrored);
  const points = face.landmarks.map(transform);
  const dense = points.length === 478;
  if (dense && allPoints) {
    ctx.fillStyle = "#9af6e4";
    ctx.beginPath();
    for (const [px, py] of points) {
      ctx.moveTo(px + 1.3, py); ctx.arc(px, py, 1.3, 0, Math.PI * 2);
    }
    ctx.fill();
    return;
  }
  const [x, y, w, h] = face.box;
  const [left, top] = transform([x, y]); const [right, bottom] = transform([x+w, y+h]);
  ctx.lineCap = "round"; ctx.lineJoin = "round";
  if (!dense) {
    ctx.strokeStyle = "#74ebde"; ctx.lineWidth = 1.5;
    ctx.setLineDash([7, 5]); ctx.strokeRect(Math.min(left, right), top, Math.abs(right-left), bottom-top); ctx.setLineDash([]);
  }
  ctx.strokeStyle = "#8be4d9"; ctx.lineWidth = 1.4;
  const paths = dense ? contours : [[0,2,1],[3,2,4],[3,4]];
  for (const path of paths) {
    ctx.beginPath(); path.forEach((index, i) => i ? ctx.lineTo(...points[index]) : ctx.moveTo(...points[index])); ctx.stroke();
  }
  ctx.fillStyle = "#c8f8ff";
  if (dense) {
    ctx.fillStyle = "#ffdc88";
    for (const index of [1,4,33,133,263,362,61,291,10,152,468,473]) {
      ctx.beginPath(); ctx.arc(...points[index], 2.2, 0, Math.PI*2); ctx.fill();
    }
  } else {
    for (const [px, py] of points) {
      ctx.beginPath(); ctx.arc(px, py, 3, 0, Math.PI*2); ctx.fill();
    }
  }
}
