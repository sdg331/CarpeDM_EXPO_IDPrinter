# 얼굴 비율 비교 실험 · 2026-10-13

2026-10-16 소유자 요청으로 기존 비율 추천을 방문자 입사 UI에도 연결했다. 운영 경로는 `/api/match/landmarks`이고, `/api/match`는 SFace 비교 기준으로 남는다. 아래 운영 SFace 유지 문장은 당시 실험 범위의 이력이다. [현재 API](API_CONTRACT.md)의 운영 MediaPipe 추천과 [D-055](DECISIONS.md)를 우선한다. 분포 보정이 사람의 닮음 검증을 뜻하지 않는다는 한계는 유지한다.

`/static/matching-lab.html`에서 사진 선택·카메라 촬영·캐릭터 기준 사진으로 같은 입력의 SFace와 MediaPipe 비율 추천을 비교한다. 남자/여자/전체 조건은 두 방식에 동일하게 적용한다. 실제 추출한478개 좌표를 사진 위에 켜서 볼 수 있다.

기존 `/api/match`, 입사·NFC·사원증은 SFace를 유지한다. 실험 결과는 세션·DB·인쇄에 연결하지 않는다. 사진·개인별 좌표는 파일로 저장하거나 외부로 전송하지 않으며 브라우저 임시 URL은 사진 변경·지우기·페이지 종료에 해제한다. 늦은 분석 응답은 무시한다.

## 계산 기준

9개 비율: 얼굴 길이/폭, 턱 너비, 눈 간격, 눈 너비, 눈 높이/너비, 코 너비, 코 길이, 입 너비, 하관 길이. 픽셀 거리의 비율을 사용해 크기·평면 회전·이동 영향을 줄인다. 고개가 좌우로 돌아간 경우에는 정면 품질 검사로 거부한다. 3차원 자세를 완전히 보정하지 않는다. 코 중심 오프셋0.25, 얼굴 최소폭40px 등은 잠정 기준이다.

현재 실사와 캐릭터의 평균/표준편차를 각각 사용해9개 특징의 상대적 위치를 맞춘다. 표준편차는 최소0.015, 실사 표준점수는±3으로 제한한다. 동일 가중 평균 제곱 거리에 공개 실사 보정 표본에서 학습한 조건별 고정 비용을 더하고 제곱근으로 순서를 계산한다. 전체/남자/여자의 비용을 각각 학습한다. 엔트로피 정규화(온도0.15)와 균등 사전분포를 사용하며 사람의 닮음 정답은 사용하지 않는다. 방문자 횟수·직전 결과·순환·무작위 배정은 없으므로 같은 사진/조건은 같은 결과다.

초기 원본 거리(캐릭터 표준편차 최소0.03)는 평가 스크립트의 자기 추천 검사와 보정 전 분포에 사용한다. 현재 보정은 실사 사진용이므로 캐릭터 기준 사진을 다시 입력했을 때 자기 자신이 추천되지 않을 수 있다. 샘플 버튼은 동작 확인용으로 표시한다. 표본 편향·표정·좌표 추정 오류가 있을 수 있으며 얼굴 인식·닮음 정확도·성별 추정값으로 해석하지 않는다.

## 설치와 실행

Intel macOS, Python3.12에서 검증했다. MediaPipe0.10.21은 NumPy1.x를 요구하므로 기존 키오스크 `.venv`에 설치하지 않는다.

```sh
cd "/Users/do_not_delay/Desktop/CarpeDM_EXPO_ID Printer/CarpeDM_EXPO_IDPrinter-complete"
.venv/bin/python -m venv .venv-landmarks
.venv-landmarks/bin/python -m pip install -r requirements-landmarks.txt
.venv/bin/python scripts/fetch_landmark_model.py
.venv-landmarks/bin/python scripts/build_face_ratios.py
.venv-landmarks/bin/python scripts/build_ratio_balance.py --faces /path/to/public/lfw --report ../output/ratio-balance/evaluation.json
KIOSK_MATCH_LAB=1 KIOSK_NFC=disabled KIOSK_PRINT=screen .venv/bin/python scripts/run_kiosk.py --host 127.0.0.1 --port 8002
```

8002 서버가 실행 중이면 해당 서버를 정상 종료하고 마지막 명령을 실행한다. `.venv-landmarks`와 `models`는 Git에서 제외한다. Google 공식 버전1 모델의 SHA256을 확인한다. `assets/face_ratios.json`에는 공개 캐릭터의 비율과 원본/성별 설정/모델 해시만 저장한다. 캐릭터를 바꾸면 기준을 재생성하며, 불일치 시 이전 기준으로 추천하지 않는다.

macOS에서는 CPU 설정에서도 그래픽 초기화가 필요했다. Codex 제한 환경에서는 실패했고 허용된 로컬 실행에서 확인했다. Pi/ARM 패키지 호환성·지연은 미검증이다. Windows는 `Scripts/python.exe`를 자동 선택하며, 인터프리터 경로는 서버 환경변수 `KIOSK_FACE_RATIO_PYTHON`으로 지정할 수 있다.

## API와 실패 처리

- GET `/api/experiments/matching/status`: enabled, configured, experimental, calibrated:false, externalUpload:false. configured는 인터프리터·모델·기준 파일 검사이며 모델 실행 성공 보증은 아니다.
- POST `/api/experiments/matching/compare`: multipart frame + character_gender(any/male/female). 기존8MiB/1,200만 픽셀 검사와 loopback/same-origin 제한을 적용한다. 실제 `/api/match`로 SFace 결과를 구하고 별도 환경의 제한된 프로세스로 비율을 계산한다.
- 비교1개만 실행하며 중복은 MATCH_COMPARISON_BUSY(409), 프로세스30초 제한이다. 취소하면 UI는 결과를 버리며 서버 계산은 최대30초 후 종료된다. 프레임은 프로세스 stdin으로 전달한다.
- 비활성403, 설정/모델/기준 오류503, 잘못된 조건422. 얼굴 없음/여러 명은 기존 SFace 오류를 유지하고 비정면/좌표 불안정은422 안내다. 오류를 임의 캐릭터나 다른 알고리즘 성공으로 바꾸지 않는다.
- sface/ratios 각각 캐릭터ID·후보 순서·처리시간, 실제 좌표478개, 같은 추천인지 여부를 반환한다. 닮음 정확도 백분율은 표시하지 않는다.

## 평가

```sh
.venv/bin/python -m pytest tests/test_face_ratios.py tests/test_character_preference.py tests/test_face.py tests/test_api_flow.py -q
npm test
.venv-landmarks/bin/python scripts/evaluate_face_ratios.py ../output/ratio-comparison-20261013/evaluation.json --faces /private/tmp/carpedm-lfw-cache/datasets/jessicali9530/lfw-dataset/versions/4 --limit 128
```

원본·반전·밝기±20%:32/32 자기 추천 통과. 공개 LFW에서 seed20261013으로 인물별 한 장128명을 선택했다.17건은 SFace 다중 얼굴,9건은 비정면으로 제외했다. 비교102건의 비율 추천은07=44,08=45,06=12,05=1로07/08 합계89/102(87.3%)였다. SFace는 같은 표본에서8종 모두 선택됐다. 추천 일치는22/102(21.6%)다. 닮음 정답이 없으므로 이 수치는 정확도가 아니다.

랜드마크 추론 중앙값은 이 Mac에서 약18.5ms(모델 기동 제외), 실제 API는 프로세스·모델 기동을 포함해 약2초대가 관측됐다. 오프라인 SFace는 별도 환경 OpenCV4.11, 현재 서버는4.14다. 실제 서버9건으로 별도 계약·실행 검증을 했다.

## 분포 보정 검증 · 2026-10-14

포함된 `assets/face_ratio_balance.json`은 현재 캐릭터용 보정이다. 그대로 사용할 수 있으며, 캐릭터 기준을 재생성하면 공개 LFW 폴더로 보정도 다시 생성한다. 자동 다운로드는 없다. 기준 파일 해시·모델·특징 순서·수치의 유효성을 검사하고 누락/불일치는 오류로 차단한다. 파일에는 집계 평균·표준편차·조건별 비용만 있으며 개인별 사진·좌표·비율·인물명은 저장하지 않는다.

같은 공개 LFW 캐시에서 인물별 한 장640명을 seed20261013으로 선택했다. 최초128명은 이전 진단 집합으로 보정에 제외했다. 이후 유효 인물의 최초100명은 검증, 나머지274명으로만 평균/표준편차와 고정 비용을 학습했다. 전체 중 다중 얼굴98명·비정면66명이 제외됐다. 검증100명은 비용 학습에 사용하지 않았으나 같은 공개 데이터셋 안의 분리이므로 전시장 방문자에 일반화됐다는 뜻은 아니다.

|후보|별도100명 보정 전|보정 후|
|---|---:|---:|
|01|0|10|
|02|0|9|
|03|0|13|
|04|0|15|
|05|0|11|
|06|7|13|
|07|49|9|
|08|44|20|

07/08 합계93%→29%. 남자02/04/06/08=23/28/17/32, 여자01/03/05/07=22/20/25/33. 이전 진단102명은07/08 합계87.3%→30.4%, 8종 모두 사용됐다. 분포 개선이며 정확한 균등이나 닮음 정확도는 보장하지 않는다. 생성 시 검증100명에서 모든 후보가 선택되고 전체 후보 최대 점유≤35%, 조건별≤50%인 경우에만 파일을 교체한다.

결과: 상위 `output/ratio-balance-20261014/evaluation.json`, [QA](qa/RATIO_BALANCE_2026-10-14.md). 기존 사원증 SFace 추천은 유지한다. 다음 단계는 사람의 닮음 평가와 한국 전시장 촬영 조건 검증이다. ImageGen·실제 Pi 검증은 이번 범위에 포함하지 않았다.

## 여러 사람이 있는 프레임 · 2026-10-14

현재 비교 요청은 SFace가 고른 가장 큰 얼굴 박스를 MediaPipe에 전달한다. 같은 대상의 랜드마크만 사용하며 일치하는 상세 얼굴이 없으면 오류로 종료한다. 카메라에는 실제 대상 박스·5점이 먼저 표시되고 결과에는 실제478점과 윤곽·눈·코·입 연결을 기본으로 표시한다. 기존 평가/보정 생성은 독립 표본 품질을 위해 여전히 단일 얼굴을 요구한다. 위의100명 분포 수치는 단일 얼굴 표본 검증이며 군중 환경 정확도를 뜻하지 않는다.
