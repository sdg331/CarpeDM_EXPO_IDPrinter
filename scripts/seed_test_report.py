"""Seed a one-hour screen-only example for an already registered NFC session."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    from backend.store import KioskStore, SessionNotFound
    from backend.test_records import TEST_RECORDS

    parser = argparse.ArgumentParser(description="등록된 카드의 퇴근 화면에 임시 예시 기록 연결")
    parser.add_argument("session_id")
    args = parser.parse_args()
    store = KioskStore()
    try:
        store.get_session(args.session_id)
        if not store.active_card(args.session_id):
            parser.error("현재 카드와 연결된 세션만 사용할 수 있습니다.")
        if store.get_mirrorting_link(args.session_id):
            parser.error("실제 MirrorTing 기록이 연결된 세션에는 예시를 넣지 않습니다.")
    except SessionNotFound:
        parser.error("등록된 세션을 찾을 수 없습니다.")
    report = {
        "session_id": 1, "mode": 5, "total_score": 82, "grade": "테스트 예시",
        "fit_scores": {
            "response": {"score": 82, "label": "핵심 전달", "summary": "생각을 간결하게 전하는 대화를 체험했어요."},
            "voice": {"score": 80, "label": "차분한 목소리", "summary": "편안한 속도로 이야기하는 모습의 예시예요."},
            "expression": {"score": 84, "label": "밝은 표현", "summary": "상대방에게 관심을 표현하는 모습의 예시예요.", "provisional": True},
            "posture": {"score": 82, "label": "편안한 자세", "summary": "자연스러운 자세로 대화하는 모습의 예시예요."},
        },
        "strengths": ["상대방의 이야기를 듣고 자신의 생각을 차분하게 전달했어요."],
        "improvements": ["다음 대화에서는 열린 질문을 한 가지 더 건네보세요."],
        "headline": {"sentence": "새로운 팀원과 즐거운 첫 대화를 나눴어요.", "context": "화면 확인을 위해 임의로 만든 테스트 기록이며 실제 분석 결과가 아닙니다."},
        "coaching": [{"issue": "대화를 이어가는 연습", "suggestion": "상대방의 의견에 질문을 덧붙여보세요."}],
        "day_ending": {"label": "오늘의 마무리", "text": "새로운 경험을 함께해주셔서 고마워요."},
    }
    TEST_RECORDS.mkdir(parents=True, exist_ok=True)
    path = TEST_RECORDS / f"{args.session_id}.json"
    # No name, card UID, portrait, or MirrorTing access token is stored here.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump({"expiresAt": time.time() + 3600, "report": report}, output, ensure_ascii=False)
    print("테스트용 예시 기록을 연결했습니다. 유효기간 1시간, 화면 미리보기 전용입니다.")
    print("KIOSK_TEST_RECORDS=1을 설정하고 서버를 다시 시작한 뒤 카드를 태그하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
