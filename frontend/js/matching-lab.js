import { characters } from "./content.js?v=20261016-final-kiosk-r1";
import { request, createLiveApi } from "./api-client.js?v=20261016-final-kiosk-r1";
import { validatePhoto } from "./photo-lab-core.js";
import { Camera } from "./camera.js?v=20261016-final-kiosk-r1";
import { drawFaceOverlay } from "./face-overlay.js?v=20261016-final-kiosk-r1";
import { validateComparison, recommendationMarkup } from "./matching-lab-core.js?v=20261016-final-kiosk-r1";

const $ = id => document.getElementById(id);
const camera = new Camera(), liveApi = createLiveApi();
let frame = null, photoURL = null, faceMap = null, epoch = 0, controller = null, configured = false;
const messages = {
  NO_PERSON: "얼굴을 찾지 못했어요. 얼굴이 선명한 정면 사진으로 다시 비교해주세요.",
  MULTIPLE_PEOPLE: "한 사람만 나온 사진을 골라주세요.",
  FACE_NOT_FRONTAL: "얼굴을 정면으로 바라보고 다시 촬영해주세요.",
  LANDMARK_QUALITY_FAILED: "얼굴 좌표가 불안정해요. 눈과 얼굴 윤곽이 잘 보이는 사진을 골라주세요.",
  LANDMARK_TIMEOUT: "분석 시간이 길어졌어요. 잠시 후 다시 비교해주세요.",
  MATCH_COMPARISON_BUSY: "이전 사진을 처리 중이에요. 잠시 후 다시 비교해주세요.",
  MATCH_LAB_DISABLED: "비교 기능이 꺼져 있어요. 로컬 실험 설정을 확인해주세요.",
  LANDMARK_ENGINE_UNAVAILABLE: "비율 분석 환경이 준비되지 않았어요. 설치와 실행 설정을 확인해주세요.",
  LANDMARK_MODEL_UNAVAILABLE: "얼굴 좌표 모델을 준비해주세요.",
  RATIO_REFERENCES_UNAVAILABLE: "현재 캐릭터의 비율 기준 데이터를 다시 만들어주세요.",
  CAMERA_UNAVAILABLE: "카메라를 사용할 수 없어요. 사진 선택으로 비교할 수 있어요.",
  INVALID_IMAGE: "JPEG·PNG·WebP 사진을 선택해주세요.",
  IMAGE_TOO_LARGE: "8 MiB·1,200만 픽셀 이하의 사진을 선택해주세요.",
};
const say = text => { $("status").textContent = text; };
const fail = error => say(messages[error.code || error.message] || "결과를 확인하지 못했어요. 사진과 로컬 서버 연결을 확인해주세요.");
const gender = () => document.querySelector('[name="gender"]:checked').value;

function setBusy(busy) {
  $("compare").disabled = busy || !configured || !frame;
  $("preferences").disabled = busy;
  $("file").disabled = busy;
  $("camera").disabled = busy;
  document.querySelectorAll('#samples button').forEach(button => { button.disabled = busy; });
}
function clearResults() {
  faceMap = null;
  $("results").hidden = true;
  $("sface-result").replaceChildren(); $("ratio-result").replaceChildren();
  $("mesh").hidden = true;
  $("mesh").width = $("mesh").height = 0;
  $("show-mesh").checked = false;
}
function cancel() { epoch++; controller?.abort(); controller = null; setBusy(false); }
function stopCamera() {
  camera.stop(); $("video").hidden = true;
  $("capture").hidden = $("cancel-camera").hidden = true;
}
function clearPhoto() {
  cancel(); stopCamera(); clearResults(); frame = null;
  if (photoURL) URL.revokeObjectURL(photoURL);
  photoURL = null;
  $("photo").removeAttribute("src"); $("photo").hidden = true;
  $("photo-empty").hidden = false; $("file").value = "";
  setBusy(false); say("사진을 지웠어요. 새 사진으로 비교할 수 있어요.");
}
async function load(blob) {
  cancel(); stopCamera(); clearResults();
  const token = epoch; let url;
  try {
    await validatePhoto(blob);
    if (token !== epoch) return;
    url = URL.createObjectURL(blob);
    const image = new Image(); image.src = url; await image.decode();
    if (image.naturalWidth * image.naturalHeight > 12_000_000) throw new Error("IMAGE_TOO_LARGE");
    if (token !== epoch) return;
    if (photoURL) URL.revokeObjectURL(photoURL);
    frame = blob; photoURL = url; url = null;
    $("photo").src = photoURL; $("photo").hidden = false; $("photo-empty").hidden = true;
    setBusy(false); say("사진이 준비됐어요. 같은 조건으로 두 추천을 비교해보세요.");
  } catch (error) { if (token === epoch) fail(error); }
  finally { if (url) URL.revokeObjectURL(url); }
}
async function startCamera() {
  clearPhoto(); const token = epoch;
  $("photo-empty").hidden = true; $("video").hidden = false;
  $("capture").hidden = $("cancel-camera").hidden = false; $("capture").disabled = true;
  say("카메라 권한을 확인하고 있어요.");
  try {
    await camera.start($("video"), liveApi, (status, detail) => {
      if (token !== epoch) return;
      if (status === "error") { stopCamera(); $("photo-empty").hidden = false; fail(new Error("CAMERA_UNAVAILABLE")); return; }
      $("capture").disabled = status !== "ready";
      faceMap = typeof detail === "object" ? detail.face : null;
      drawFaceOverlay($("mesh"), faceMap);
      say(status === "ready" ? faceMap?.count > 1 ? `${faceMap.count}명 중 가까운 얼굴을 선택했어요. 선택된 분이 정면을 봐주세요.` : "얼굴이 잘 보여요. 촬영할 수 있어요." : "카메라 앞으로 조금 더 가까이 와주세요.");
    });
  } catch (error) { if (token === epoch) { stopCamera(); $("photo-empty").hidden = false; fail(error); } }
}
function drawMesh() {
  drawFaceOverlay($("mesh"), faceMap, { visible: !$("video").hidden || $("show-mesh").checked });
}
async function compare() {
  if (!frame || !configured || controller) return;
  cancel(); clearResults();
  const token = epoch, selectedGender = gender(), current = new AbortController(); controller = current;
  setBusy(true); say("같은 사진을 두 방식으로 분석하고 있어요.");
  liveApi.detectPreview(frame, { signal: current.signal }).then(data => {
    if (token !== epoch || faceMap?.source === "mediapipe") return;
    faceMap = data.face; drawFaceOverlay($("mesh"), faceMap);
  }).catch(() => {});
  try {
    const form = new FormData(); form.append("frame",frame,"comparison.jpg"); form.append("character_gender",selectedGender);
    const data = await request("/api/experiments/matching/compare", { method:"POST",body:form,signal:current.signal,timeout:35000 });
    if (token !== epoch) return;
    if (!data.ok) throw new Error({ no_face:"NO_PERSON",multiple_faces:"MULTIPLE_PEOPLE" }[data.error] || "INVALID_RESPONSE");
    validateComparison(data,selectedGender);
    $("sface-result").innerHTML = recommendationMarkup(data.sface);
    $("ratio-result").innerHTML = recommendationMarkup(data.ratios);
    faceMap = { ...data.face, source: "mediapipe", landmarks: data.ratios.landmarks };
    $("show-mesh").checked = true; drawMesh();
    $("agreement").textContent = data.sface.characterId === data.ratios.characterId
      ? "두 방식이 같은 캐릭터를 추천했어요. 실제로 닮았는지도 확인해주세요."
      : "두 추천이 달라요. 얼굴형과 눈·코·입을 보며 어느 쪽이 더 닮았는지 비교해주세요.";
    $("results").hidden = false;
    say(`${data.face.count > 1 ? `${data.face.count}명 중 가까운 얼굴을 선택했어요. ` : ""}비교를 마쳤어요. 비율 추천은 실사와 그림의 차이·후보 분포를 보정한 실험 결과예요.`);
  } catch (error) { if (token === epoch && error.name !== "AbortError") fail(error); }
  finally { if (token === epoch) { controller = null; setBusy(false); } }
}
$("samples").innerHTML = characters.map(c=>`<button data-id="${c.id}" aria-label="캐릭터 ${c.id.slice(-2)} 사진 사용"><img src="${c.thumbnail}" alt=""></button>`).join("");
$("samples").addEventListener("click", async event => {
  const button = event.target.closest('button[data-id]'); if (!button || button.disabled) return;
  cancel(); const token = epoch;
  try { const response = await fetch(characters.find(c=>c.id===button.dataset.id).image); if (!response.ok) throw new Error("INVALID_IMAGE"); const blob = await response.blob(); if (token===epoch) await load(blob); }
  catch(error) { if (token===epoch) fail(error); }
});
$("file").addEventListener("change",event=>{ if (event.target.files[0]) load(event.target.files[0]); });
$("camera").addEventListener("click",startCamera);
$("cancel-camera").addEventListener("click",clearPhoto);
$("capture").addEventListener("click",async()=>{ $("capture").disabled = true; try { await load(await camera.capture()); } catch(error) { fail(error); $("capture").disabled = false; } });
$("compare").addEventListener("click",compare); $("clear").addEventListener("click",clearPhoto);
$("preferences").addEventListener("change",()=>{ cancel(); clearResults(); say("추천 조건을 바꿨어요. 다시 비교해주세요."); });
$("show-mesh").addEventListener("change",drawMesh); $("photo").addEventListener("load",drawMesh);
addEventListener("resize",drawMesh); addEventListener("pagehide",clearPhoto);
request("/api/experiments/matching/status",{timeout:4000,cache:"no-store"}).then(data=>{
  configured = data.enabled === true && data.configured === true;
  setBusy(false); say(configured ? "사진을 선택하거나 촬영해 비교해보세요." : "비교 기능의 설치·실행 설정이 필요해요. README의 얼굴 비율 실험 안내를 확인해주세요.");
}).catch(fail);
