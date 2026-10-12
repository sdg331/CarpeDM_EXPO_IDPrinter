# 여성 캐릭터 얼굴 구분 수정 — 2026-10-11 r4

이 문서는 이전 r4 기록이다. 최신은 [재수정 r5](FEMALE_REFINE_2026-10-11.md) 참조.

05: 둥근 볼·짧고 둥근 턱·작은 눈·두꺼운 일자 눈썹·넓은 입.
07: 긴 얼굴·각진 턱·작은 아몬드형 눈·긴 코·절제된 미소.
내장 image_gen으로 얼굴을 수정했다. 편집 프롬프트: ../output/portraits8-distinct-female-20261011/PROMPTS.md.
헤어/의상과 같은 시리즈 느낌을 유지하도록 요청했으며, 생성 특성상 세부 렌더링 차이가 있다.
원본/직전 자산은 보존했다. 나머지 6명 PNG/WebP 바이트 동일 확인.

## 적용 파일 및 재생성

assets/characters/char_05.png, char_07.png와 WebP, framing.json, prototypes.npz,
print 8장과 sweep, frontend JS/HTML 캐시 r4, README 및 이 기록.
기존 prepare_character_assets.py → build_prototypes.py → make_print_assets.py 및 --sweep 재사용.
원본1086×1448 RGB, WebP192×256, 인쇄288×384 mode1, 벡터8×128.
머리 여백 검출: 4.97%, 5.32%, 5.04%, 4.97%, 4.97%, 4.97%, 4.97%, 4.97%.
얼굴 높이 범위: 44.31%–47.08%.
정수리 여백 목표5%, 얼굴 높이 목표45%, 등비 확대/이동; 머리 잘림 없는 비교판/화면 시각 확인.

## 검증

- pytest tests/test_face.py tests/test_badge.py tests/test_api_flow.py tests/test_lfw_evaluation.py -q: 47 passed, 1 skipped, 기존 Starlette/httpx 경고1.
- 독립 스타일 표본 없음(style_n=0): 관련 독립 스타일 품질 검증 skip.
- preflight.py: 소프트웨어 항목 모두 PASS.
- 8012 서버를 새 벡터로 재시작; screen 프린터/disabled NFC.
- 캐릭터8명 원본/밝기/축소/흑백 32개 API 테스트 통과; WebP8장 HTTP 응답 바이트 일치; 빈 이미지 no_face.
- 브라우저 화면: r4 WebP8장 로드, 가로 넘침 없음. 저장 introduction-800x1280.jpg (미리보기 설정 영역 포함).
- 코드 구조/알고리즘 변경은 없음. 이전 프런트엔드 전체 테스트는 이번 이미지 변경에서 반복하지 않음.

## 실제 사람 LFW 선택 집중도

데이터셋 jessicali9530/lfw-dataset v4. 고정 seed20261011, 인물당 한 장씩1000명.
보정용200명/평가800명 인물 분리. 통과161/660명, 다중 얼굴39/140명 제외.
표본 manifest SHA256: 12bfff03d5fc8358d91e2b0161235abf35d380efe6d2ee0a5fa1795af15163e1.
최종 벡터 SHA256: b4ded3b40cad8803e3d3181d553f2419fd32871976fe316f2af5e599d1846037.
현재 운영 선택수: {'char_01': 76, 'char_02': 100, 'char_03': 66, 'char_04': 69, 'char_05': 74, 'char_06': 46, 'char_07': 140, 'char_08': 89}.
8종 모두 선택, 최대비중21.2%(07번). 근접마진183/660=27.7%, 직전223/660=33.8%.
최대비중은 직전15.2%에서 증가했다. 균등 선택이나 닮음 정확도 향상을 의미하지 않는다.
별도 보정후보195/660=29.5%, 최대15.9%; 운영에 적용하지 않음.
근접마진<25% 진단 기준은 아직 미달. 실제 사진의 정답 캐릭터가 없으므로 정확도/인구집단 공정성 검증 아님.
실물 감열 출력, Pi 카메라/처리시간, 관람객 재촬영 일관성은 미검증.
