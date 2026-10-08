# API Contract · 2026-10-03

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

| status | 의미 |
| --- | --- |
| `preview` | 메모리 미리보기. `physicalOutput:false`, `completionConfirmed:false`, `previewUrl` 제공 |
| `submitted` | ESC/POS 또는 CUPS로 전송. `physicalOutput:true`, `completionConfirmed:false` |
| `confirmed` | 로컬 운영자가 실물을 확인하고 결과 불명 작업을 해소함. 두 플래그 true |

`GET /api/print/previews/{previewId}`는 PNG를 반환한다. 기본 5분 후 410 `PREVIEW_EXPIRED`다.

`GET /api/operations/{operationId}`는 읽기 전용이며 `{ok,operationId,kind,sessionId,status,errorCode,retryable,result}`를 반환한다. 저장 상태는 `running`, `success`, `retryable_error`, `unknown`, `error`다. 출력 성공의 `result.status`를 따로 확인한다.

장치 접근 후 오류·서버 재시작으로 결과를 모르면 `UNKNOWN_OUTCOME`이다. 운영 CLI가 실물 확인 후 처리하도록 [운영 절차](OPERATIONS.md)를 따른다. 출력을 확인해도 카드 회수가 확인된 것은 아니므로 카드 연결은 자동 해제하지 않는다.

기존 `POST /api/issue`는 기본 410 `LEGACY_ENDPOINT_DISABLED`다. `KIOSK_ENABLE_LEGACY_ISSUE=1`과 `KIOSK_PRINT=screen`을 함께 설정한 개발 환경만 허용한다.

## MirrorTing 보고서

키오스크에 `KIOSK_MIRRORTING_URL`과 32자 이상 `KIOSK_BRIDGE_TOKEN`을 설정하고, MirrorTing 백엔드에 [동반 패치](../integrations/mirrorting/README.md)를 적용해야 한다. 설정 존재는 실제 연결 검증을 의미하지 않는다.

서버 간 경로는 `X-Bridge-Token` 헤더를 요구한다. 브라우저에 토큰을 넘기지 않는다.

- `GET /api/integrations/mirrorting/cards/{uid}` → 현재 카드의 키오스크 `sessionId` 스냅샷.
- `POST /api/integrations/mirrorting/link` → `{sessionId,cardUid,mirrorSessionId,accessToken}`. 스냅샷과 현재 카드 연결이 다르면 409다.
- `GET /api/reports/{sessionId}` → 연결된 실제 MirrorTing `/progress`를 확인한 후 `/report` 조회. `X-Session-Token`은 키오스크 서버에서만 사용한다.
- `POST /api/reports/print` → `{operationId,sessionId,reportId}`. 원본 보고서 세션 ID와 일치할 때만 출력한다.

조회 결과:

```text
ok, status:available, source:mirrorting,
sessionId, mirrorSessionId, reportId,
totalScore, grade, modeMinutes,
fitScores.{response,voice,expression,posture,eye}.{score,label,summary,provisional,observation},
strengths[], improvements[], headline.{sentence,context},
dayEnding.{label,text}, coaching[].{issue,suggestion}
```

누락 점수는 0으로 만들지 않는다. eye 관측값과 잠정 평가 표기를 유지한다. 미완료는 `REPORT_PENDING`, 기록 없음은 `REPORT_NOT_FOUND`, 미설정은 `INTEGRATION_PENDING`이며 샘플 피드백으로 대체하지 않는다. 키오스크 팀과 MirrorTing 체험 직무는 별개다.
