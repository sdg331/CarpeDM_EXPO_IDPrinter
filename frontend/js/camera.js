import { KioskError } from "./api-client.js";

export class Camera {
  stream = null;
  generation = 0;
  timer = null;
  controller = null;
  video = null;
  async start(video, api, onState) {
    this.stop();
    const generation = this.generation;
    this.video = video;
    this.controller = new AbortController();
    const signal = this.controller.signal;
    onState("initializing");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 960 },
          facingMode: "user",
        },
        audio: false,
      });
      if (generation !== this.generation) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      this.stream = stream;
      video.srcObject = stream;
      await video.play();
      if (generation !== this.generation) return;
      const detect = async () => {
        if (generation !== this.generation) return;
        try {
          const frame = await this.capture(480);
          const result = await api.detectPreview(frame, { signal });
          if (generation !== this.generation) return;
          if (!Number.isInteger(result.count) || result.count < 0)
            throw new KioskError("INVALID_RESPONSE");
          onState(
            result.count === 0
              ? "no_person"
              : result.count > 1
                ? "multiple_people"
                : result.ok
                  ? "ready"
                  : "no_person",
          );
          this.timer = setTimeout(detect, 650);
        } catch (error) {
          if (generation === this.generation && error.name !== "AbortError")
            onState("error", error.code || "BACKEND_UNAVAILABLE");
        }
      };
      await detect();
    } catch {
      if (generation === this.generation)
        onState("error", "CAMERA_UNAVAILABLE");
    }
  }
  async capture(maxSide = 1280) {
    if (!this.video?.videoWidth || !this.video?.videoHeight)
      throw new KioskError("CAMERA_UNAVAILABLE");
    const scale = Math.min(
      1,
      maxSide / Math.max(this.video.videoWidth, this.video.videoHeight),
    );
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(this.video.videoWidth * scale);
    canvas.height = Math.round(this.video.videoHeight * scale);
    canvas
      .getContext("2d")
      .drawImage(this.video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve, reject) =>
      canvas.toBlob(
        (blob) => {
          canvas.width = canvas.height = 0;
          blob ? resolve(blob) : reject(new KioskError("CAMERA_UNAVAILABLE"));
        },
        "image/jpeg",
        0.88,
      ),
    );
  }
  stop() {
    this.generation++;
    clearTimeout(this.timer);
    this.controller?.abort();
    this.stream?.getTracks().forEach((t) => t.stop());
    if (this.video) this.video.srcObject = null;
    this.stream = null;
    this.video = null;
  }
}
