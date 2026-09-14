"""pytest 공통 설정 — 프로젝트 루트를 import 경로에 넣는다.

실행:  ./.venv/bin/pytest tests/ -v
전제:  assets/prototypes.npz 가 있어야 한다 (build_prototypes.py).
       카메라·프린터·실제 얼굴 사진은 필요 없다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
