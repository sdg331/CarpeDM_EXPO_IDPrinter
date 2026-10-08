export const MAX_BYTES = 8 * 1024 * 1024;
export const MAX_PIXELS = 12_000_000;

// Inspect dimensions before asking the browser to decode a compressed image.
export function photoInfo(bytes) {
  const u = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  const v = new DataView(u.buffer, u.byteOffset, u.byteLength);
  let width, height, type;
  if (u.length >= 24 && [137,80,78,71,13,10,26,10].every((n,i)=>u[i]===n)) {
    width = v.getUint32(16); height = v.getUint32(20); type = "image/png";
  } else if (u[0] === 255 && u[1] === 216) {
    let p = 2;
    while (p + 4 < u.length) {
      if (u[p++] !== 255) break;
      while (u[p] === 255) p++;
      const marker = u[p++];
      if (marker === 0xda || marker === 0xd9) break;
      if (marker === 0xd8 || (marker >= 0xd0 && marker <= 0xd7)) continue;
      if (p + 2 > u.length) break;
      const size = v.getUint16(p);
      if (size < 2 || p + size > u.length) break;
      if ([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker) && size >= 8) {
        height = v.getUint16(p + 3); width = v.getUint16(p + 5); type = "image/jpeg"; break;
      }
      p += size;
    }
  } else if (u.length >= 30 && String.fromCharCode(...u.slice(0,4)) === "RIFF" && String.fromCharCode(...u.slice(8,12)) === "WEBP") {
    const chunk = String.fromCharCode(...u.slice(12,16));
    if (chunk === "VP8X") {
      width = 1 + u[24] + (u[25]<<8) + (u[26]<<16);
      height = 1 + u[27] + (u[28]<<8) + (u[29]<<16);
    } else if (chunk === "VP8 " && u[23] === 157 && u[24] === 1 && u[25] === 42) {
      width = v.getUint16(26,true) & 0x3fff; height = v.getUint16(28,true) & 0x3fff;
    } else if (chunk === "VP8L" && u[20] === 47) {
      width = 1 + u[21] + ((u[22]&63)<<8);
      height = 1 + (u[22]>>6) + (u[23]<<2) + ((u[24]&15)<<10);
    }
    type = "image/webp";
  }
  if (!width || !height || Math.min(width,height) < 16) throw new Error("INVALID_IMAGE");
  if (width * height > MAX_PIXELS) throw new Error("IMAGE_TOO_LARGE");
  return {width,height,type};
}

export async function validatePhoto(blob) {
  if (!blob?.size) throw new Error("INVALID_IMAGE");
  if (blob.size > MAX_BYTES) throw new Error("IMAGE_TOO_LARGE");
  return photoInfo(await blob.arrayBuffer());
}

export function cropRect(width, height, zoom = 1, x = 0.5, y = 0.5) {
  if (![width,height,zoom,x,y].every(Number.isFinite) || width <= 0 || height <= 0) throw new Error("INVALID_IMAGE");
  const w = Math.min(width,height * 0.75) / Math.max(1,Math.min(2.5,zoom));
  const h = w / 0.75;
  return {x:(width-w)*Math.max(0,Math.min(1,x)),y:(height-h)*Math.max(0,Math.min(1,y)),width:w,height:h};
}

export function canvasBlob(canvas, type = "image/png") {
  return new Promise((resolve,reject)=>canvas.toBlob(blob=>blob ? resolve(blob) : reject(new Error("IMAGE_FAILED")),type,0.9));
}

export class PhotoCamera {
  constructor(mediaDevices = globalThis.navigator?.mediaDevices, timeout = 15000) {
    this.mediaDevices = mediaDevices; this.timeout = timeout; this.generation = 0; this.stream = null;
  }
  async start(video, onEnded = ()=>{}) {
    this.stop();
    const generation = this.generation;
    if (!this.mediaDevices?.getUserMedia) throw new Error("CAMERA_UNAVAILABLE");
    let timer;
    try {
      const pending = this.mediaDevices.getUserMedia({video:{facingMode:"user",width:{ideal:1280},height:{ideal:960}},audio:false});
      const waiting = new Promise((_,reject)=>{
        this.cancelStart = ()=>reject(new Error("CANCELLED"));
        timer = setTimeout(()=>reject(new Error("CAMERA_UNAVAILABLE")),this.timeout);
      });
      pending.then(stream=>{if (generation !== this.generation) stream.getTracks().forEach(t=>t.stop());},()=>{});
      const stream = await Promise.race([pending,waiting]);
      if (generation !== this.generation) {stream.getTracks().forEach(t=>t.stop());return false;}
      this.stream = stream; this.video = video; video.srcObject = stream;
      const interrupted = ()=>{if (generation === this.generation) {this.stop();onEnded();}};
      stream.addEventListener("inactive",interrupted,{once:true});
      stream.getVideoTracks().forEach(t=>t.addEventListener("ended",interrupted,{once:true}));
      await Promise.race([video.play(),waiting]);
      return generation === this.generation;
    } catch (error) {
      if (generation !== this.generation) return false;
      this.stop(); throw new Error("CAMERA_UNAVAILABLE");
    } finally {clearTimeout(timer);if (generation === this.generation) this.cancelStart = null;}
  }
  async capture(canvas) {
    if (!this.stream?.active || !this.stream.getVideoTracks().some(t=>t.readyState === "live") || !this.video?.videoWidth || !this.video?.videoHeight) throw new Error("CAMERA_UNAVAILABLE");
    const generation = this.generation;
    const scale = Math.min(1,1280 / Math.max(this.video.videoWidth,this.video.videoHeight));
    canvas.width = Math.round(this.video.videoWidth*scale); canvas.height = Math.round(this.video.videoHeight*scale);
    canvas.getContext("2d").drawImage(this.video,0,0,canvas.width,canvas.height);
    try {
      const blob = await canvasBlob(canvas,"image/jpeg");
      if (generation !== this.generation) throw new Error("CANCELLED");
      return blob;
    } finally {canvas.width = canvas.height = 0;}
  }
  stop() {
    this.generation++; this.cancelStart?.(); this.cancelStart = null;
    this.stream?.getTracks().forEach(t=>t.stop());
    if (this.video) this.video.srcObject = null;
    this.stream = this.video = null;
  }
}
