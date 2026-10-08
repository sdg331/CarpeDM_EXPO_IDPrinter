import test from "node:test";
import assert from "node:assert/strict";
import {cropRect,photoInfo,validatePhoto,PhotoCamera,MAX_BYTES} from "../../frontend/js/photo-lab-core.js";

function png(width,height) {
  const bytes=new Uint8Array(24);bytes.set([137,80,78,71,13,10,26,10]);const view=new DataView(bytes.buffer);view.setUint32(16,width);view.setUint32(20,height);return bytes;
}
test("framing stays inside landscape and portrait sources without stretching",()=>{
  for(const [width,height] of [[1280,720],[720,1280],[1086,1448]]) for(const zoom of [1,1.6,2.5]) for(const x of [0,.5,1]) for(const y of [0,.5,1]) {
    const crop=cropRect(width,height,zoom,x,y);
    assert.ok(Math.abs(crop.width/crop.height-.75)<1e-10);
    assert.ok(crop.x>=0 && crop.y>=0 && crop.x+crop.width<=width+1e-8 && crop.y+crop.height<=height+1e-8);
  }
  assert.throws(()=>cropRect(0,900));
  assert.throws(()=>cropRect(720,960,NaN));
});
test("file headers reject oversized decompression and non-photo input before decode",async()=>{
  assert.deepEqual(photoInfo(png(720,960)),{width:720,height:960,type:"image/png"});
  assert.throws(()=>photoInfo(png(4000,4000)),/IMAGE_TOO_LARGE/);
  assert.throws(()=>photoInfo(new TextEncoder().encode('<svg onload="bad"></svg>')),/INVALID_IMAGE/);
  assert.throws(()=>photoInfo(png(0,960)),/INVALID_IMAGE/);
  await assert.rejects(validatePhoto({size:MAX_BYTES+1,arrayBuffer:()=>assert.fail("read oversized file")}),/IMAGE_TOO_LARGE/);
});
test("JPEG and all supported WebP header formats are recognized",()=>{
  const jpg=Uint8Array.from([255,216,255,192,0,17,8,3,192,2,208,3,1,17,0,2,17,0,3,17,0]);
  assert.deepEqual(photoInfo(jpg),{width:720,height:960,type:"image/jpeg"});
  for(const kind of ["VP8X","VP8 ","VP8L"]) {
    const b=new Uint8Array(30);b.set(new TextEncoder().encode("RIFF"));b.set(new TextEncoder().encode("WEBP"),8);b.set(new TextEncoder().encode(kind),12);const v=new DataView(b.buffer);
    if(kind==="VP8X"){b[24]=207;b[25]=2;b[27]=191;b[28]=3;}
    if(kind==="VP8 "){b.set([157,1,42],23);v.setUint16(26,720,true);v.setUint16(28,960,true);}
    if(kind==="VP8L"){b[20]=47;b[21]=207;b[22]=194;b[23]=239;}
    assert.deepEqual(photoInfo(b),{width:720,height:960,type:"image/webp"});
  }
});
function stream() {
  const track={readyState:"live",stops:0,stop(){this.stops++;this.readyState="ended";},addEventListener(){}};
  return {active:true,getTracks:()=>[track],getVideoTracks:()=>[track],addEventListener(){},track};
}
test("cancelled camera permission releases a late stream",async()=>{
  let resolve;const camera=new PhotoCamera({getUserMedia:()=>new Promise(r=>resolve=r)});
  const starting=camera.start({play:async()=>{}});camera.stop();assert.equal(await starting,false);
  const late=stream();resolve(late);await Promise.resolve();assert.ok(late.track.stops>=1);assert.equal(camera.stream,null);
});
test("camera denial, startup timeout and playback error release resources",async()=>{
  await assert.rejects(new PhotoCamera({getUserMedia:()=>{throw Error("synchronous denial");}}).start({}),/CAMERA_UNAVAILABLE/);
  await assert.rejects(new PhotoCamera({getUserMedia:async()=>{throw Error("denied");}}).start({}),/CAMERA_UNAVAILABLE/);
  let resolve;const timed=new PhotoCamera({getUserMedia:()=>new Promise(r=>resolve=r)},5);
  await assert.rejects(timed.start({}),/CAMERA_UNAVAILABLE/);const late=stream();resolve(late);await Promise.resolve();assert.ok(late.track.stops>=1);
  const live=stream();const camera=new PhotoCamera({getUserMedia:async()=>live});
  await assert.rejects(camera.start({play:async()=>{throw Error("playback");}}),/CAMERA_UNAVAILABLE/);
  assert.ok(live.track.stops>=1);
});
test("camera captures a bounded frame and clears its temporary canvas",async()=>{
  const live=stream();const camera=new PhotoCamera({getUserMedia:async()=>live});
  await camera.start({videoWidth:2560,videoHeight:1920,play:async()=>{}});
  let size;
  const canvas={getContext:()=>({drawImage:(...args)=>{size=args.slice(3);}}),toBlob(callback){callback(new Blob(["synthetic"],{type:"image/jpeg"}));}};
  const blob=await camera.capture(canvas);
  assert.equal(blob.type,"image/jpeg");assert.deepEqual(size,[1280,960]);assert.equal(canvas.width,0);assert.equal(canvas.height,0);
  camera.stop();assert.ok(live.track.stops>=1);
});
