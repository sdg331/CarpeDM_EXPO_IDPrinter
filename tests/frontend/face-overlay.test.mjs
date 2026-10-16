import test from "node:test";
import assert from "node:assert/strict";
import { overlayTransform, validateFace, drawFaceOverlay } from "../../frontend/js/face-overlay.js";
import { Camera } from "../../frontend/js/camera.js";
import { createState } from "../../frontend/js/state.js";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const face=()=>({count:2,selection:"largest_visible_face",source:"yunet",imageSize:[640,480],
  box:[.2,.1,.4,.7],landmarks:[[.3,.3],[.5,.3],[.4,.4],[.3,.5],[.5,.5]]});

test("Actual face coordinates follow contain, cover and horizontal mirroring",()=>{
  assert.deepEqual(overlayTransform(640,480,320,320)([0,0]),[0,40]);
  assert.deepEqual(overlayTransform(640,480,320,320)([1,1]),[320,280]);
  const normal=overlayTransform(640,480,320,320,"cover")([.25,.5]);
  const mirrored=overlayTransform(640,480,320,320,"cover",true)([.25,.5]);
  assert.ok(Math.abs(normal[0]+mirrored[0]-320)<1e-9);assert.equal(normal[1],160);
});
test("Missing or malformed face data never produces a centered decorative map",()=>{
  const canvas={hidden:false,width:100,height:100};drawFaceOverlay(canvas,null);
  assert.equal(canvas.hidden,true);assert.equal(canvas.width,0);
  assert.equal(validateFace(face()).count,2);
  const invalid=face();invalid.landmarks[0]=[NaN,.5];assert.throws(()=>validateFace(invalid));
  drawFaceOverlay(canvas,invalid);assert.equal(canvas.hidden,true);
});
test("Camera forwards the selected face and enables multi-person capture",async()=>{
  const oldNavigator=globalThis.navigator,oldDocument=globalThis.document;
  const track={readyState:"live",addEventListener(){},stop(){}};
  const stream={active:true,getTracks:()=>[track],getVideoTracks:()=>[track],addEventListener(){}};
  Object.defineProperty(globalThis,"navigator",{value:{mediaDevices:{getUserMedia:async()=>stream}},configurable:true});
  globalThis.document={createElement:()=>({getContext:()=>({drawImage(){}}),toBlob:callback=>callback(new Blob(["frame"]))})};
  const camera=new Camera(),states=[];
  try {
    await camera.start({videoWidth:640,videoHeight:480,play:async()=>{}},
      {detectPreview:async()=>({ok:true,count:2,face:face()})},(...state)=>states.push(state));
    assert.equal(states.at(-1)[0],"ready");assert.equal(states.at(-1)[1].face.count,2);
  } finally {camera.stop();Object.defineProperty(globalThis,"navigator",{value:oldNavigator,configurable:true});globalThis.document=oldDocument;}
});
test("Late matching points cannot replace a new visitor's captured face",async()=>{
  const state=createState(),original=new Blob(["first"]),renders=[];
  state.patch({screen:"processing",aiMode:"A",capture:original,busy:true});
  let onFace;
  const controller=new AbortController();
  const context={state,validateFace,
    drawAnalysisFace:()=>renders.push(state.data.captureFace),
    isSameOriginImage:()=>true,location:{href:"http://127.0.0.1:8002/"},
    api:{faceMap:()=>assert.fail("Matching must not launch a duplicate landmark request"),
      matchCharacter:async(_,ctx)=>{onFace=ctx.onFace;ctx.onFace(face());return {kind:"A",image:"/assets/characters/char_01.png"};}},
    run:async(_,task,success)=>{success(await task({signal:controller.signal}));},
    go:()=>state.patch({screen:"resultA",busy:false,capture:null,captureFace:null})};
  const source=readFileSync(new URL("../../frontend/js/app.js",import.meta.url),"utf8");
  runInNewContext(source.slice(source.indexOf("function analyze()"),source.indexOf("function finishNfc(")),context);
  context.analyze();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(renders.length,1);
  state.reset();state.patch({screen:"processing",capture:new Blob(["second"]),busy:true});
  onFace({...face(),source:"mediapipe",landmarks:Array.from({length:478},()=>[.5,.5])});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(renders.length,1);assert.equal(state.data.captureFace,null);
});

test("Dense maps retain real contours and twelve anchors without covering the face in dots",()=>{
  let dots=0,boxes=0;
  const ctx={scale(){},setLineDash(){},strokeRect(){boxes++;},beginPath(){},moveTo(){},lineTo(){},stroke(){},arc(){dots++;},fill(){}};
  const canvas={parentElement:{clientWidth:640,clientHeight:480},getContext:()=>ctx};
  drawFaceOverlay(canvas,{...face(),source:"mediapipe",landmarks:Array.from({length:478},()=>[.5,.5])});
  assert.equal(dots,12);assert.equal(boxes,0);
  dots=0;drawFaceOverlay(canvas,face());
  assert.equal(dots,5);assert.equal(boxes,1);
});

test("Processing draws all 478 measured points in one fill and keeps toggling safe",()=>{
  const arcs=[],moves=[];let fills=0;
  const ctx={scale(){},beginPath(){},moveTo:(...p)=>moves.push(p),arc:(...p)=>arcs.push(p),fill(){fills++;}};
  const canvas={parentElement:{clientWidth:320,clientHeight:480},getContext:()=>ctx};
  const measured={...face(),source:"mediapipe",landmarks:Array.from({length:478},(_,i)=>[i/478,.5])};
  drawFaceOverlay(canvas,measured,{allPoints:true,mirrored:true});
  assert.equal(arcs.length,478);assert.equal(moves.length,478);assert.equal(fills,1);
  assert.equal(arcs[0][0],320);assert.equal(arcs[0][1],240);
  assert.ok(arcs[477][0]<1);
  drawFaceOverlay(canvas,measured,{allPoints:true,visible:false});
  assert.equal(canvas.hidden,true);assert.equal(canvas.width,0);
  assert.equal(arcs.length,478);
});
