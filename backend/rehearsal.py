"""Clearly labelled checkout examples; never returned as live visitor records."""
from backend.reports import normalize_report


def example_report():
    report = normalize_report("EXPO-DEMO-001", 1, {
        "session_id": 1, "grade": "성장", "total_score": 82.4, "mode": 5,
        "fit_scores": {
            "response": {"score": 85, "label": "응답", "summary": "의견을 먼저 말하고 구체적인 이유를 덧붙였어요."},
            "voice": {"score": None, "label": "목소리", "summary": "이 예시에서는 측정하지 않았어요."},
            "expression": {"score": 79, "label": "표정", "summary": "대화 상대를 향해 편안한 표정을 유지했어요.", "provisional": True},
            "posture": {"score": 83, "label": "자세", "summary": "상대에게 몸을 향하고 안정된 자세로 이야기했어요.", "provisional": True},
            "eye": {"score": None, "label": "시선", "summary": "상대를 바라보며 이야기를 들었어요.", "observation": True},
        },
        "strengths": ["요점을 먼저 이야기하고 경험을 예로 들었어요.", "상대의 의견을 듣고 질문으로 확인했어요."],
        "improvements": ["답변을 조금 짧게 정리하면 메시지가 더 잘 전달돼요."],
        "headline": {"sentence": "경청에서 시작해, 나의 생각을 한 문장으로.", "context": "새로운 팀원과 첫 협업을 준비한 대화 예시예요."},
        "coaching": [{"issue": "첫 업무 대화", "suggestion": "요점 → 이유 → 다음 행동 순서로 이야기해보세요."}],
        "day_ending": {"label": "오늘의 마무리", "text": "나의 강점을 발견한 오늘, 다음 대화에서도 한 걸음 더 나아가요."},
    })
    report.update(source="demo_sample", sample=True)
    return report
