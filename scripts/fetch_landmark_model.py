"""Download only the pinned official Google model; preserve old file on failure."""
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.face_ratios import MODEL, MODEL_SHA256

url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
if MODEL.is_file() and hashlib.sha256(MODEL.read_bytes()).hexdigest() == MODEL_SHA256:
    print("Pinned landmark model already present")
else:
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(8 * 1024 * 1024 + 1)
    if hashlib.sha256(data).hexdigest() != MODEL_SHA256:
        raise SystemExit("Model checksum mismatch; existing model preserved")
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    temporary = MODEL.with_suffix(".tmp")
    temporary.write_bytes(data)
    temporary.replace(MODEL)
    print("Saved verified Google face_landmarker.task")
