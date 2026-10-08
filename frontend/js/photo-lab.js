import {cropRect,validatePhoto,canvasBlob,PhotoCamera} from "./photo-lab-core.js";

const $ = id=>document.getElementById(id);
const camera = new PhotoCamera();
let source = null, sourceURL = null, resultURL = null, epoch = 0, request = null, ready = false;
const downloads = new Map();
const messages = {
  INVALID_IMAGE:"사진을 읽지 못했어요. JPEG·PNG·WebP 파일을 선택해주세요.",
  IMAGE_TOO_LARGE:"8 MiB·1,200만 픽셀 이하의 사진을 선택해주세요.",
  CAMERA_UNAVAILABLE:"카메라를 사용할 수 없어요. 권한을 확인하거나 사진 선택·휴대폰 촬영을 이용해주세요.",
  PHOTO_LAB_DISABLED:"로컬 서버에서 사진 실험을 켜주세요. 실행 방법은 README를 확인해주세요.",
  PHOTO_ENGINE_UNAVAILABLE:"로컬 얼굴 모델이 준비되지 않았어요. 프레이밍은 계속 사용할 수 있어요.",
  NO_PERSON:"얼굴을 찾지 못했어요. 한 사람의 얼굴이 선명하게 보이는 사진을 선택해주세요.",
  MULTIPLE_PEOPLE:"한 사람이 나온 사진으로 다시 시험해주세요.",
  PHOTO_QUALITY_FAILED:"얼굴을 정면에서 밝고 선명하게 촬영해주세요. 원본 프레이밍은 그대로예요.",
};
function message(text,error=false) {$("message").textContent=text;$("message").setAttribute("role",error?"alert":"status");}
function fail(error) {message(messages[error.message] || "처리하지 못했어요. 로컬 서버 연결을 확인한 뒤 다시 시험해주세요.",true);}
function clearResult() {
  $("result").removeAttribute("src");$("result").hidden=true;
  $("result-empty").hidden=false;$("result-label").textContent="아직 실행하지 않았어요";
  if (resultURL) URL.revokeObjectURL(resultURL);
  resultURL=null;$("download-result").disabled=true;
}
function cancelRequest() {epoch++;request?.abort();request=null;$("cancel-process").hidden=true;$("compose").disabled=!ready||!source;}
function draw() {
  if (!source) return;
  const c = $("framed");c.width=720;c.height=960;
  const r = cropRect(source.naturalWidth,source.naturalHeight,+$("zoom").value,+$("offset-x").value/100,+$("offset-y").value/100);
  c.getContext("2d").drawImage(source,r.x,r.y,r.width,r.height,0,0,720,960);
}
async function load(blob) {
  cancelRequest();camera.stop();$("camera-panel").hidden=true;
  const token=epoch;let url;
  message("사진을 읽고 있어요.");
  try {
    await validatePhoto(blob);
    if (token!==epoch) return;
    url=URL.createObjectURL(blob);
    const image=new Image();image.src=url;
    try {await image.decode();} catch {throw new Error("INVALID_IMAGE");}
    if (token!==epoch) return;
    if (image.naturalWidth*image.naturalHeight>12_000_000) throw new Error("IMAGE_TOO_LARGE");
    if (sourceURL) URL.revokeObjectURL(sourceURL);
    source=image;sourceURL=url;url=null;clearResult();
    $("zoom").value=1;$("offset-x").value=$("offset-y").value=50;
    $("editor").hidden=false;$("compose").disabled=!ready;draw();
    message("확대와 위치를 조절해보세요. 얼굴·옷을 새로 생성하지 않습니다.");
  } catch (error) {if (token===epoch) fail(error);}
  finally {if (url) URL.revokeObjectURL(url);}
}
function clear() {
  cancelRequest();camera.stop();$("camera-panel").hidden=true;clearResult();
  if (sourceURL) URL.revokeObjectURL(sourceURL);
  source=sourceURL=null;$("framed").width=$("framed").height=0;
  $("editor").hidden=true;$("photo-file").value=$("phone-file").value="";
  for (const [url,timer] of downloads) {clearTimeout(timer);URL.revokeObjectURL(url);}
  downloads.clear();message("사진을 지웠어요. 새 사진을 선택할 수 있어요.");
}
async function startCamera() {
  cancelRequest();const token=epoch;
  $("camera-panel").hidden=false;$("capture").disabled=true;
  message("카메라 권한을 확인하고 있어요.");
  try {
    const started=await camera.start($("camera"),()=>{ $("camera-panel").hidden=true;fail(new Error("CAMERA_UNAVAILABLE")); });
    if (!started||token!==epoch) return;
    $("capture").disabled=false;message("한 사람의 얼굴과 어깨를 화면 안에 맞춰주세요.");
  } catch (error) {if (token===epoch) {$("camera-panel").hidden=true;fail(error);}}
}
async function compose() {
  if (!source||!ready||request) return;
  cancelRequest();const token=epoch;const controller=new AbortController();request=controller;
  $("compose").disabled=true;$("cancel-process").hidden=false;clearResult();
  message("로컬 서버에서 배경과 구도를 정리하고 있어요.");
  const timer=setTimeout(()=>controller.abort(),30000);
  try {
    const blob=await canvasBlob($("framed"));
    if (token!==epoch) return;
    const response=await fetch("/api/experiments/photo/compose",{method:"POST",headers:{"Content-Type":"image/png"},body:blob,signal:controller.signal,cache:"no-store"});
    if (!response.ok) {const data=await response.json();throw new Error(data.error?.code||"IMAGE_FAILED");}
    if (!response.headers.get("content-type")?.startsWith("image/png")) throw new Error("INVALID_IMAGE");
    const result=await response.blob();const info=await validatePhoto(result);
    if (info.width!==720||info.height!==960||info.type!=="image/png") throw new Error("INVALID_IMAGE");
    if (token!==epoch) return;
    const url=URL.createObjectURL(result);
    try {const image=new Image();image.src=url;await image.decode();} catch {URL.revokeObjectURL(url);throw new Error("INVALID_IMAGE");}
    if (token!==epoch) {URL.revokeObjectURL(url);return;}
    resultURL=url;$("result").src=url;$("result").hidden=false;$("result-empty").hidden=true;
    $("result-label").textContent="로컬 CV · 정장 생성 아님";
    $("download-result").disabled=false;message("배경·구도 정리를 마쳤어요. 얼굴·옷과 경계가 자연스러운지 비교해주세요.");
  } catch(error) {if (token===epoch) {if (error.name==="AbortError") message("시간이 초과됐어요. 원본은 그대로예요. 다시 시험해주세요.",true);else fail(error);}}
  finally {clearTimeout(timer);if (token===epoch) {request=null;$("cancel-process").hidden=true;$("compose").disabled=!ready;}}
}
function downloadURL(url,name) {const a=document.createElement("a");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();}
$("download").addEventListener("click",async()=>{
  const token=epoch;
  try {const blob=await canvasBlob($("framed"));if(token!==epoch)return;const url=URL.createObjectURL(blob);downloadURL(url,"photo-framed.png");downloads.set(url,setTimeout(()=>{URL.revokeObjectURL(url);downloads.delete(url);},1000));}catch(error){fail(error);}
});
$("download-result").addEventListener("click",()=>{if(resultURL)downloadURL(resultURL,"photo-local-cv.png");});
for (const id of ["photo-file","phone-file"]) {
  $(id).addEventListener("change",()=>{const file=$(id).files[0];$(id).value="";if(file)load(file);});
  $(id).addEventListener("cancel",()=>message("사진 선택을 취소했어요. 기존 사진은 그대로예요."));
}
for (const id of ["zoom","offset-x","offset-y"]) $(id).addEventListener("input",()=>{cancelRequest();clearResult();draw();});
$("sample").addEventListener("click",async()=>{
  cancelRequest();const token=epoch;let url;
  try {
    const response=await fetch("/assets/characters/char_01.png",{cache:"no-store"});
    if(!response.ok)throw new Error("INVALID_IMAGE");
    const blob=await response.blob();if(token!==epoch)return;
    url=URL.createObjectURL(blob);const image=new Image();image.src=url;await image.decode();
    if(token!==epoch)return;
    const canvas=document.createElement("canvas");canvas.width=720;canvas.height=960;
    const ctx=canvas.getContext("2d");ctx.fillStyle="#dcdcdc";ctx.fillRect(0,0,720,960);
    ctx.drawImage(image,160,96,400,400*image.naturalHeight/image.naturalWidth);
    const example=await canvasBlob(canvas);canvas.width=canvas.height=0;
    if(token===epoch)await load(example);
  } catch(error){if(token===epoch)fail(error);}
  finally {if(url)URL.revokeObjectURL(url);}
});
$("camera-open").addEventListener("click",startCamera);$("retake").addEventListener("click",startCamera);
$("camera-cancel").addEventListener("click",()=>{cancelRequest();camera.stop();$("camera-panel").hidden=true;message("촬영을 취소했어요. 기존 사진은 그대로예요.");});
$("capture").addEventListener("click",async()=>{const token=epoch;$("capture").disabled=true;try {const blob=await camera.capture(document.createElement("canvas"));if(token===epoch)await load(blob);}catch(error){if(token===epoch)fail(error);}finally{if(token===epoch)$("capture").disabled=false;}});
$("compose").addEventListener("click",compose);$("clear").addEventListener("click",clear);
$("cancel-process").addEventListener("click",()=>{cancelRequest();message("처리를 취소했어요. 원본 프레이밍은 그대로예요.");});
addEventListener("pagehide",clear);
async function refreshStatus() {
  try {const response=await fetch("/api/experiments/photo/status",{cache:"no-store"});if(!response.ok)throw new Error();const data=await response.json();ready=data.ready===true&&data.enabled===true;$("engine-status").textContent=ready?"로컬 모델 준비 완료 · 외부 AI 전송 없음":"프레이밍은 사용 가능해요. 배경 정리는 README에 따라 로컬 서버와 모델을 준비해주세요.";}
  catch {$("engine-status").textContent="브라우저 프레이밍만 사용할 수 있어요. 배경 정리는 로컬 FastAPI 서버가 필요해요.";}
  $("compose").disabled=!ready||!source;
}
refreshStatus();
