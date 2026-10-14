# API Contract · 2026-10-03

## 얼굴 비율 비교 실험 · 2026-10-13

2026-10-14: 비율 추천에 고정된 실사/그림 표준화와 조건별 분포 보정을 적용한다. 상태 및 ratios 결과의 `distributionCorrected:true`는 분포 보정 적용 여부이며 `calibrated:false`는 사람이 평가한 닮음 검증이 없음을 유지한다. `ranking[].distance`는 보정된 비용의 제곱근으로 작을수록 우선이며 SFace 점수와 직접 비교하지 않는다. 보정 파일 누락/오래된 기준/잘못된 수치는503 또는 configured:false로 차단한다. 방문자 횟수·이전 결과는 사용하지 않는다.

`KIOSK_MATCH_LAB=1`일 때만 POST `/api/experiments/matching/compare`로 같은 multipart frame과 character_gender를 SFace·MediaPipe 비율 방식에 전달한다. GET `/api/experiments/matching/status`는 활성화 및 로컬 설치 파일 상태를 반환한다. 동시1개·30초 프로세스 제한, 기존 사진 크기/loopback/same-origin 검사, 메모리 처리와 no-store 계약을 적용한다. 결과는 실험 전용이며 사원증과 세션에 적용하지 않는다. 실제 좌표와 두 추천을 반환하며 닮음 백분율은 없다. [전체 계약·오류·설치](FACE_RATIO_EXPERIMENT.md).

## 캐릭터 추천 조건 · 2026-10-13

`POST /api/match` multipart에 선택적 `character_gender:any|male|female`를 추가한다. 기본값은 `any`이며 다른 값은 422로 거부한다. 방문자의 성별을 추정하지 않는다. `assets/characters/genders.json`의 캐릭터 설정으로 후보를 제한하고 그 안에서 가장 높은 점수를 선택한다. `top`은 기존 전체 캐릭터 배열의 인덱스다. `raw`는 기존 전체 점수를 유지하며 `order`와 `margin`은 선택된 후보 기준이다. `display`는 제외된 후보가 0이며 선택된 후보의 합이 100이다. 응답에 `characterGender`를 반환한다. 후보가 없으면 `AI_UNAVAILABLE`이며 전체 후보로 자동 변경하지 않는다.

추천 조건은 현재 브라우저 상태에만 보관한다. 재촬영은 유지하고 새 방문자 초기화에서는 `any`로 되돌린다. NFC/DB에는 추가 저장하지 않는다. 결과 화면의 직접 선택은 기존처럼 8명 전체를 허용한다.

운영자가 명시적으로 연 `?rehearsal=checkout`은 퇴근 한 번만 카드 없이 실제 카메라로 촬영하고 시연용 예시 리포트를 인쇄한다. 촬영·재촬영·취소가 가능하며 다음 일반 퇴근은 실제 카드 조회다. 이 모드는 `POST /api/souvenirs/start`의 `purpose:rehearsal`로 발급한 임시 인화 권한을 사용한다. 실제 체험 기록이나 카드 등록으로 가장하지 않으며 인쇄물의 제목과 출처에 예시를 표시한다.

## 선택 사진 실험

`/static/photo-lab.html` 전용이며 기존 발급 흐름에서 호출하지 않는다. `GET /api/experiments/photo/status`는 `enabled`, `ready`, `processing:local_cv`, `generatesFace:false`, `generatesSuit:false`, `externalUpload:false`를 반환한다. `KIOSK_PHOTO_LAB=1`일 때만 `POST /api/experiments/photo/compose`가 동작한다. 요청은 multipart가 아닌 JPEG/PNG/WebP 원시 바이트, 최대 8 MiB이며 전체 디코딩 전에 기존 1,200만 픽셀 제한을 확인한다. 성공은 720×960 PNG이며 세션·이미지 저장소·NFC·인쇄를 변경하지 않는다. 모든 방문자 API와 같은 loopback·출처·no-store 제한을 따른다. 오류는 `PHOTO_LAB_DISABLED`, `PHOTO_ENGINE_UNAVAILABLE`, `NO_PERSON`, `MULTIPLE_PEOPLE`, `PHOTO_QUALITY_FAILED`, `PHOTO_PROCESSING_FAILED` 또는 기존 이미지 오류다. [실험 사용과 한계](PHOTO_LAB.md)를 따른다.

현재 통합 코드 기준이다. UI·API는 같은 출처의 FastAPI 서버에서 제공한다. 프런트 샘플(`?sample=1`)은 이 실제 장치 계약을 실행하지 않는다.

## 공통

- 방문객 `/api/*`는 loopback 접속만 허용한다. 원격에서 사용할 수 있는 API는 토큰 인증을 요구하는 `/api/integrations/mirrorting/*`다.
- JSON 변경 요청은 `Content-Type: application/json`을 사용한다.
- `operationId`는 8~128자다. NFC 등록·출력 재시도는 최초 ID를 유지한다.
- 같은 작업 ID를 다른 입력에 재사용하면 `OPERATION_CONFLICT`다.
- 다른 ID를 발급해도 같은 세션의 배지/리포트 출력은 각각 한 작업으로 제한한다.
- API 응답은 `Cache-Control: no-store`다. 다른 출처의 변경 요청은 거부한다.
- 일반 오류: `{ "ok": false, "error": { "code": "PROFILE_EXPIRED", "retryable": true } }`.
- HTTP 성공과 실물 출력 완료는 다른 상태다. `retryable`이 false인 출력은 자동 반복하지 않는다.

## 모델·카메라

| 경로 | 요청 | 반환 / 의미 |
| --- | --- | --- |
| `GET /api/health` | 없음 | 모델·캐릭터·보정·DB·NFC·프린터·리포트 연결 설정 상태 |
| `GET /api/characters` | 없음 | 8개 캐릭터 메타데이터 |
| `POST /api/detect` | multipart `frame` | `ok`, `count`, `confidence` |
| `POST /api/match` | multipart `frame` | `top`, `characters`, `display`, `order`, `raw`, `margin`, `confidence`, `elapsed_ms`, `calibrated` |
| `POST /api/profile/generate` | multipart `frame`, `operationId` | `kind:B`, `profileId`, `image`, `previewUrl`, `elapsedMs`, `reused`, `expiresInSeconds` |
| `GET /api/profile/{profileId}/image` | 없음 | 메모리 PNG, 만료 시 410 `PROFILE_EXPIRED` |
| `DELETE /api/profile/{profileId}` | 없음 | 프로필 메모리 제거 |

프레임은 최대 8 MiB다. A의 기존 얼굴 오류는 HTTP 200의 `ok:false,error:"no_face"` 또는 `multiple_faces`로 반환한다. 어댑터가 이를 도메인 오류로 변환한다. `raw`는 진단값이며 관람객 화면에 노출하지 않는다. 표시 점수는 확률이나 성격·능력 평가가 아니다.

B는 얼굴·의상을 유지하는 로컬 CV 배경/구도 처리다. 의상 생성은 구현하지 않았다. `/api/profile`은 동일한 생성 계약의 별칭이다. 생성 작업 ID와 이미지 내용이 같으면 유효기간 안에서 기존 결과를 반환한다.

## NFC 등록과 배지

`POST /api/nfc/register`:

```json
{
  "operationId": "nfc-unique-request-id",
  "name": "김미래",
  "teamId": "development",
  "aiMode": "A",
  "result": { "kind": "A", "characterId": "char_01" }
}
```

B는 `aiMode:"B"`, `result:{"kind":"B","profileId":"서버가 반환한 ID"}`를 사용한다. 이름은 앞뒤 공백 제외 1~10자이며 제어문자를 거부한다. 팀 ID는 `development`, `ai`, `design`, `planning`, `marketing`, `hr`다.

성공: `{ "ok":true, "status":"verified", "sessionId":"서버 발급 ID", "nfcBackend":"pcsc" }`.

카드 UID를 읽어 SQLite 세션과 연결한다. 카드 메모리에 방문객 정보를 쓰지 않는다. 동일 카드 재등록은 이전 연결을 비활성화한다. `nfcBackend:mock`은 명시적 통합 테스트용이다.

- `POST /api/nfc/resolve`: `{operationId}` → 현재 카드의 `{ok,sessionId,name,teamId}`.
- `POST /api/sessions/{sessionId}/profile`: `{profileId}` → B 만료 시 같은 카드·세션의 새 촬영 결과로 교체한다. 이미 실행·성공·결과 불명인 출력은 우회할 수 없다.
- `POST /api/badge/print`: `{operationId,sessionId}` → 아래 출력 계약.

## 출력과 복구

출력 반환에는 `printJobId`, `backend`, `status`, `physicalOutput`, `completionConfirmed`가 있다.

`KIOSK_PRINT=disabled`는 명시적인 출력 비활성화 설정이다. `/api/health`의 프린터 상태는 `ready:false`, `physicalOutput:false`, `completionConfirmed:false`와 비활성화 안내를 반환한다. 출력은 미리보기나 장치 제출 없이 기존 `PRINT_UNAVAILABLE` 오류로 거절하며, 설정을 고친 뒤 같은 작업 ID로 재시도할 수 있다.

| status | 의미 |
| --- | --- |
| `preview` | 메모리 미리보기. `physicalOutput:false`, `completionConfirmed:false`, `previewUrl` 제공 |
| `submitted` | ESC/POS 또는 CUPS로 전송. `physicalOutput:true`, `completionConfirmed:false` |
| `confirmed` | 로컬 운영자가 실물을 확인하고 결과 불명 작업을 해소함. 두 플래그 true |

`GET /api/print/previews/{previewId}`는 PNG를 반환한다. 기본 5분 후 410 `PREVIEW_EXPIRED`다.

`GET /api/operations/{operationId}`는 읽기 전용이며 `{ok,operationId,kind,sessionId,status,errorCode,retryable,result}`를 반환한다. 저장 상태는 `running`, `success`, `retryable_error`, `unknown`, `error`다. 출력 성공의 `result.status`를 따로 확인한다.

장치 접근 후 오류·서버 재시작으로 결과를 모르면 `UNKNOWN_OUTCOME`이다. 오류 화면에는 해당 요청의 `운영 확인용 작업 ID`를 표시한다. 운영 CLI가 실물 확인 후 처리하도록 [운영 절차](OPERATIONS.md)를 따른다. 2026-10-13부터 정상 리포트 출력 응답(preview/submitted) 또는 운영자의 printed 확인 시 퇴근 완료와 카드 연결 해제를 같은 DB 트랜잭션에 저장한다. badge_print·사진 전용 인화는 이 초기화 대상이 아니다. 출력 오류/UNKNOWN_OUTCOME/not_printed 확인에서는 연결을 유지한다. UID는 변경하지 않으며 카드 메모리를 지우는 동작은 없다. 카드 회수와 용지 배출은 별도로 확인한다.

기존 `POST /api/issue`는 기본 410 `LEGACY_ENDPOINT_DISABLED`다. `KIOSK_ENABLE_LEGACY_ISSUE=1`과 `KIOSK_PRINT=screen`을 함께 설정한 개발 환경만 허용한다.

## MirrorTing 보고서

키오스크에 `KIOSK_MIRRORTING_URL`과 32자 이상 `KIOSK_BRIDGE_TOKEN`을 설정하고, MirrorTing 백엔드에 [동반 패치](../integrations/mirrorting/README.md)를 적용해야 한다. 설정 존재는 실제 연결 검증을 의미하지 않는다.

서버 간 경로는 `X-Bridge-Token` 헤더를 요구한다. 브라우저에 토큰을 넘기지 않는다.

- `GET /api/integrations/mirrorting/cards/{uid}` → 현재 카드의 키오스크 `sessionId` 스냅샷.
- `POST /api/integrations/mirrorting/link` → `{sessionId,cardUid,mirrorSessionId,accessToken}`. 스냅샷과 현재 카드 연결이 다르면 409다.
- `GET /api/reports/{sessionId}` → 연결된 실제 MirrorTing `/progress`를 확인한 후 `/report` 조회. `X-Session-Token`은 키오스크 서버에서만 사용한다.
- `POST /api/reports/print` → `{operationId,sessionId,reportId}`. 원본 보고서 세션 ID와 일치할 때만 출력한다.
- `POST /api/reports/print-photo` → multipart `operationId,sessionId,reportId,frame`. 확인한 사진을 같은 리포트에 포함하며 기존 JSON 경로와 세션당 1회 출력 방지를 공유한다.

조회 결과:

```text
ok, status:available, source:mirrorting,
sessionId, mirrorSessionId, reportId,
totalScore, grade, modeMinutes,
fitScores.{response,voice,expression,posture,eye}.{score,label,summary,provisional,observation},
strengths[], improvements[], headline.{sentence,context},
dayEnding.{label,text}, coaching[].{issue,suggestion},
careerTip.{id,title,body,source,note}
```

누락 점수는 0으로 만들지 않는다. eye 관측값과 잠정 평가 표기를 유지한다. 미완료는 `REPORT_PENDING`, 기록 없음은 `REPORT_NOT_FOUND`, 미설정은 `INTEGRATION_PENDING`이며 샘플 피드백으로 대체하지 않는다. 키오스크 팀과 MirrorTing 체험 직무는 별개다.

리포트 출력 이미지는 기존 576도트·1비트 규격을 유지하고, 받아들인 강점/개선 항목의 줄바꿈을 계산해 높이를 정한다. 긴 유효 리포트도 마지막 결말까지 포함한다. 출처 문구는 화면/종이에 표시하지 않으며 내부 검증용 출처 데이터는 유지한다. 인쇄 글자는 최소 24px, 본문 28px이며 실제 감열지에서 가독성을 확인한다.

`careerTip`은 MirrorTing 분석과 별도로 키오스크가 선택하는 센터 첨삭 요약이다. 방문자마다 7개 중 하나이며 같은 세션에서는 미리보기·출력·재시도에 동일하다. 사진은 8 MiB/1,200만 픽셀·JPEG/PNG/WebP 검증 후 전체 프레임을 인쇄하며 원본을 DB에 넣지 않는다. [문구·인쇄 기준](REPORT_PHOTO_TIPS.md).

## 전용 NFC 카드 사진 · 2026-10-12

2026-10-13 변경: HOME의 사진만 찍기는 NFC를 사용하지 않는다. `POST /api/souvenirs/start`에 `{operationId}`를 보내 임시 인화 권한을 받는다. 기존 인화 계약을 재사용하며 소개 주소 미설정 시 `qrPreviewUrl:null`이다. 사진 아래에는 작품 소개를 인쇄한다. 같은 operationId 재요청은 같은 유효 권한을 반환한다.

`POST /api/nfc/reset`은 `{ok:true}`를 반환하고 진행 중 NFC 읽기를 취소한다. 이전 요청은 `NFC_READ_CANCELLED`이며 새로운 요청은 초기화 완료 후 진행한다. 카드 UID·세션·체험 기록을 삭제하지 않는다.

- `POST /api/nfc/resolve`: 기존 `{operationId}`에 선택적 `purpose:checkout|souvenir` 추가. 전용 카드면 `{ok,kind:souvenir,photoPass,printJobId,qrPreviewUrl}`를 반환한다. 사원 세션/UID는 반환하지 않는다.
- `GET /api/souvenirs/{photoPass}/qr`: 승인된 소개 주소 QR PNG, no-store.
- `POST /api/souvenirs/{photoPass}/print`: multipart `frame`, 기존 8 MiB/1,200만 픽셀·JPEG/PNG/WebP 검증. 서버가 승인에 고정한 `souvenir-{photoPass}` ID로 1회 인화한다. 기존 preview/submitted/confirmed 계약을 사용한다.
- `DELETE /api/souvenirs/{photoPass}`: 메모리 승인·관련 화면 출력 미리보기 제거. DB의 출력 중복 방지 기록은 유지한다.

모든 경로는 기존 loopback/same-origin 제한을 따른다. 승인은 10분/최대 8개, 사진 DB·다운로드 서버·외부 업로드는 없다. 소개 주소는 서버 설정에서 고정하고 QR에 개인정보를 포함하지 않는다. [설정](SOUVENIR.md).

## 전시 얼굴 선택·실제 특징점 · 2026-10-14

- `POST /api/detect`: 얼굴이1명 이상이면 ok:true. count는 전체 YuNet 검출 수이며, 선택 대상의 confidence와 face를 반환한다. 임베딩은 실행하지 않는다.
- 선택 기준은 이미지 안에서 보이는 얼굴 박스 면적이 가장 큰 사람이다. 면적 동률이면 중앙에 가까운 얼굴, 신뢰도 순서다. 실제 거리 센서나 신원 추적은 아니다.
- `POST /api/match`: 같은 기준으로 SFace 임베딩을 만들고 기존 추천 조건·점수 계약과 face를 반환한다. 얼굴이 없으면 기존 no_face. offline/embed_single 및 B 합성의 엄격한 단일 얼굴 정책은 유지한다.
- face: `{count,selection:largest_visible_face,source:yunet|mediapipe,imageSize:[width,height],box:[x,y,width,height],landmarks:[[x,y],...]}`. 좌표는 원본 이미지 기준 정규화, 좌우 반전 전이다. YuNet은 눈2·코·입 양끝5개, MediaPipe는478개다.
- `POST /api/face-map`: 같은 multipart frame, 선택 얼굴의 실제 좌표를 반환한다. `{ok,face,detailAvailable,externalUpload:false}`. 별도 MediaPipe 환경이 없거나 잠겨 있거나 상세 좌표가 실패하면 실제 YuNet5개를 반환한다. 임의 좌표·다른 사람의 좌표로 대체하지 않는다. 얼굴 없음은 ok:false/error:no_face, 기타 사진 검증은 기존 크기·형식 오류다.
- 상세 작업은 비교 실험과 같은 잠금을 사용하고 프로세스8초 제한이다. 기본 매칭은 상세 맵 실패 때문에 실패하지 않는다. 모든 사진·좌표는 메모리에서 처리하며 no-store·loopback·same-origin 정책을 유지한다.
- 비교 API는 SFace가 선택한 박스를 상세 워커에 전달한다. MediaPipe가 여러 얼굴을 찾으면 그 박스와 가장 겹치는 얼굴을 사용하고 겹침이 부족하면 명시적 오류다. 각각 다른 사람을 비교하지 않는다.

## 명시적인 카드별 테스트 기록 · 2026-10-07

운영자가 요청한 화면 확인용 예시는 `scripts/seed_test_report.py <sessionId>`로 현재 활성 카드 세션에만 생성한다. `KIOSK_TEST_RECORDS=1`일 때 `data/test_records/<sessionId>.json`을 읽으며 기본 1시간 후 조회에서 제외한다. 원본 이름·UID·사진·토큰은 이 파일에 넣지 않는다. Git에서도 제외한다.

실제 MirrorTing 링크가 없는 해당 세션에만 적용하며 실제 링크·조회 오류를 예시로 대체하지 않는다. 반환은 `source:local_test`, `sample:true`, `reportId:TEST-<sessionId>`, `mirrorSessionId:null`이다. 퇴근 조회와 리포트 화면은 `테스트용 예시`를 명시한다. 예시 기록에는 인쇄 버튼을 제공하지 않으며 출력 API도 409 `TEST_REPORT_PREVIEW_ONLY`로 차단한다. 기능을 끄려면 `KIOSK_TEST_RECORDS=0`으로 변경하고 서버를 다시 시작한다.
