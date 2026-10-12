# 05·07 자연스러운 얼굴 재수정 — 2026-10-11 r5

사용자 피드백: 05의 얼굴이 부자연스럽고 05/07 구분이 부족함.
05는 최초 첨부 원본을 바탕으로 부풀어 보이는 볼/눈썹과 가늘어진 눈을 되돌렸다.
07은 직전 원본을 바탕으로 더 길고 좁은 눈, 또렷한 광대/턱선, 긴 코로 구분했다.
내장 image_gen 사용. 원본/직전 자산 보존. 프롬프트는 ../output/portraits8-female-refine-20261011/PROMPTS.md.
생성 결과의 미적 만족도는 사용자 판단이 필요하며 객관적 품질 향상으로 단정하지 않는다.

## 적용

원본: ../output/portraits8-female-refine-20261011/source.
직전 백업: ../completion-backups/portraits8-before-female-refine-20261011.
PNG/WebP05·07, framing.json, 특징벡터8×128, 감열8장 및 sweep 재생성.
나머지6명의 PNG/WebP 바이트 동일 확인. frontend 캐시r5, README/QA 갱신.
prepare_character_assets.py → build_prototypes.py → make_print_assets.py 및 --sweep.
정수리 여백5%/얼굴높이45% 기존 허용오차 검사 통과. 얼굴 왜곡 없는 등비 확대/이동.

## 검증

pytest tests/test_face.py tests/test_badge.py tests/test_api_flow.py tests/test_lfw_evaluation.py -q:
47 passed, 1 skipped, 기존 Starlette/httpx 경고1.
독립 스타일 표본없음(style_n=0) 관련 검증skip. 운영 실사 보정 미적용.
8012 서버 새 벡터로 재시작, screen 프린터/disabled NFC.
32/32 원본·밝기·축소·흑백 API 자기매칭 통과, WebP8장 바이트 일치, 빈 이미지no_face.
최종 정규화 pair.jpg와 before-after.jpg 시각 확인. 이번에는 브라우저 전체 화면 검사를 반복하지 않았다.

## LFW 재평가

동일seed20261011, 인물1000명 중 보정161/평가660명 통과, 보정/평가 인물 분리.
manifest SHA256: 12bfff03d5fc8358d91e2b0161235abf35d380efe6d2ee0a5fa1795af15163e1.
벡터 SHA256: 0feffe8a7547bcbde1f01aec3b52443920f8b9203312dae4bd6cbfcbd9d8320f.
운영 선택수: {'char_01': 87, 'char_02': 94, 'char_03': 65, 'char_04': 72, 'char_05': 63, 'char_06': 51, 'char_07': 136, 'char_08': 92}.
8종 선택. 최대비중20.6%(07), 직전21.2%.
근접마진225/660=34.1%, 직전183/660=27.7%보다 증가. 목표<25% 미달.
보정후보201/660=30.5%, 최대16.1%; 운영미적용.
외형 변경이 매칭 정확도 향상을 보장하지 않으며 선택 집중도/점수 안정성 진단이다.
K-FACE 원본 데이터 대기 상태는 유지. 실제 관람객 닮음 정답, Pi카메라, 실물감열 출력은 미검증.
