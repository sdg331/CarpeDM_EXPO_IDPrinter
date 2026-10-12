"""Short paraphrases of the career center teacher's red corrections."""

from random import Random

CAREER_SOURCE = "동양미래대학교 취업지원센터"
CAREER_NOTE = "선생님 첨삭 내용을 짧게 정리했어요."
CAREER_TIPS = (
    ("업무의 방향부터 확인하세요.", "혼자 판단하기 어려운 핵심 정보부터 질문하세요. 미팅의 대상과 목적, 기준으로 삼을 자료, 완성 시점을 확인하면 좋아요."),
    ("늦어질 것 같다면 미리 공유하세요.", "마감 전에 현재 진행 상태, 지연 원인, 예상 영향을 보고하세요. 먼저 공유할 수 있는 부분과 최종본 전달 계획도 함께 제안해보세요."),
    ("실수는 해결 계획과 함께 보고하세요.", "팀장에게 실수 사실과 현재 상황, 해결에 필요한 시간을 먼저 알리세요. 수정 후에는 바뀐 부분을 명확히 표시해 전달하세요."),
    ("수정 방향을 다시 말해 확인하세요.", "피드백을 먼저 받아들이고, 이해한 수정 방향을 자신의 말로 다시 설명하세요. 애매한 기준은 질문해 확인하면 좋아요."),
    ("겹친 업무는 우선순위를 조율하세요.", "긴급 요청이 팀장과 조율된 일인지 먼저 확인하세요. 조율되지 않았다면 두 업무의 상황을 간단히 보고하고 우선순위를 확인하세요."),
    ("업무 전화도 미리 연습해보세요.", "전화 응대의 예의와 방법도 연습해두세요. 텍스트 소통에 익숙하더라도 업무 전화에 대응하는 연습이 필요해요."),
    ("기억보다 기록을 남기세요.", "업무 지시를 받을 때 메모하세요. 자주 하는 업무는 나만의 체크리스트로 만들면 실수를 줄이고 업무 속도를 높일 수 있어요."),
)


def career_tip(session_id: str) -> dict[str, str]:
    # A session-seeded draw keeps the preview and every retry on the same tip.
    index = Random(session_id).randrange(len(CAREER_TIPS))
    title, body = CAREER_TIPS[index]
    return {"id": f"{index + 1:02d}", "title": title, "body": body,
            "source": CAREER_SOURCE, "note": CAREER_NOTE}
