# AI Mode B — Face-preserving Formal Profile Integration — 2026-10-01

## 1. Status

CURRENT product decision:
- external cloud generative image API 사용하지 않음
- visitor의 얼굴 identity를 유지
- local computer vision 기반으로 사원증용 포멀 프로필을 생성
- live frontend integration은 아직 구현되지 않음

현재 frontend의 `createLiveApi().generateProfile()`은 integration adapter가 없어서 `INTEGRATION_PENDING`이 정상이다.

## 2. UX Promise

사용자에게 약속할 표현:
- `촬영한 얼굴은 그대로 유지하면서 사원증에 어울리는 프로필을 만들어드려요.`

피할 표현:
- `AI가 새로운 얼굴을 생성합니다`
- 실제로 사용하지 않는 생성형 모델 이름
- 사실과 다른 "100% 동일" 표현

목표는 "identity generation"이 아니라 **face-preserving profile composition**이다.

## 3. Recommended Architecture

```text
Browser / Kiosk UI
    │ capture frame
    ▼
FastAPI
    │
    ├─ validate request / operation context
    ├─ profile engine adapter
    │     ├─ LocalCVEngine (P0)
    │     └─ LocalGpuEngine (optional future)
    │
    ├─ temporary output store
    └─ same-origin preview endpoint
          │
          ▼
Frontend RESULT B
```

Frontend는 engine 종류를 알 필요가 없다.

## 4. P0 Engine — Deterministic Local CV

EXPO 안정성 우선 구현.

Pipeline:
1. face/person detection
2. one-person validation
3. crop / orientation / basic quality check
4. face/shoulder anchor estimation
5. foreground/background separation if available
6. neutral formal-suit transparent template placement
7. scale/position/warp adjustment
8. background cleanup
9. color/exposure normalization
10. output quality gate
11. temporary preview creation

Important:
- 얼굴 자체를 새로 생성하지 않음
- 성별 추론으로 옷을 선택하지 않음
- neutral formal template 우선
- 실패 시 임의 결과를 만들지 않고 재촬영/복구 UX 제공

## 5. Engine Abstraction

Backend concept:

```python
class ProfileEngine:
    def generate(self, frame, context) -> ProfileResult:
        ...
```

Possible implementations:
- `LocalCVEngine`: OpenCV + local detection/segmentation/template composite
- `LocalGpuEngine`: local network GPU worker or same-machine GPU worker

프론트/API 계약은 engine 변경과 무관하게 유지한다.

## 6. Optional Local GPU Upgrade

P0 품질이 부족할 때만 검토한다.

Architecture:
```text
Pi / Kiosk Browser
  → Pi FastAPI broker
    → trusted local-LAN GPU worker
      → result
    → same-origin frontend result
```

Rules:
- cloud dependency 없음
- worker unavailable 시 명확한 error
- P0 LocalCV fallback 가능하면 유지
- 행사 네트워크가 불안정하면 GPU worker를 필수 단일 경로로 만들지 않음
- 실제 모델/VRAM/latency를 측정하기 전 품질 향상을 확정 사실처럼 문서화하지 않음

## 7. API Contract — MVP Proposal

### Option A — synchronous MVP

`POST /api/profile/generate`

Multipart:
- `frame`: JPEG
- `operationId`: stable request id

Response:

```json
{
  "ok": true,
  "kind": "B",
  "profileId": "profile_001",
  "image": "/api/profile/profile_001/image",
  "elapsedMs": 4120
}
```

Frontend normalization target:

```js
{
  kind: "B",
  image: "/api/profile/profile_001/image",
  profileId: "profile_001"
}
```

This shape works with the current `app.js` result validation because it already expects `result.kind === "B"` and a same-origin `result.image`.

### Option B — truthful staged job

Use only if real stage visibility is needed.

`POST /api/profile/jobs`
→ `202 Accepted`

```json
{
  "ok": true,
  "jobId": "profile_job_001",
  "status": "queued"
}
```

`GET /api/profile/jobs/{jobId}`

```json
{
  "ok": true,
  "status": "running",
  "stage": "compose"
}
```

Allowed stages:
- validate
- detect
- prepare
- compose
- finalize
- quality_check
- success
- error

Frontend displays a stage only when backend reports it.
No fake percentage.

## 8. Frontend Adapter

Target addition in `frontend/js/live-integrations.js`:

```js
generateProfile(frame, context) {
  const form = new FormData();
  form.append("frame", frame, "capture.jpg");
  form.append("operationId", context.operationId);
  return postMultipart("/api/profile/generate", form, context);
}
```

The existing flow remains:

```text
SCR-08 CAMERA
  → SCR-09 AI_PROCESSING
  → api.generateProfile(frame)
  → SCR-11 AI_RESULT_B
```

No IA change required.

## 9. Processing UI

MVP synchronous engine:
- use indeterminate motion
- copy: `사원증에 어울리는 프로필을 준비하고 있어요.`
- do not rotate through fake technical stages

If job-stage backend exists:
- 얼굴 확인
- 인물 정리
- 의상 적용
- 프로필 마무리

Visitor-facing words should be simpler than backend stage names.

## 10. Result B UI

Recommended sequence:
1. result image enters slightly blurred
2. blur resolves
3. `프로필이 완성됐어요`
4. name/team context
5. `이 사진으로 사원증 만들기`
6. continue to NFC

Optional retake:
- only after retry/session rules are defined
- must not accidentally duplicate downstream NFC/print work

## 11. Quality Gate

Fail rather than show obviously broken output.

Check candidates:
- exactly one face
- face region present after composition
- face not occluded by suit layer
- head/shoulder crop inside safe region
- output dimensions valid
- output file readable
- no empty/transparent final image

Advanced similarity check is optional and must be benchmarked before use.

## 12. Error Codes

Proposed:
- `PROFILE_ENGINE_UNAVAILABLE`
- `PROFILE_TIMEOUT`
- `PROFILE_QUALITY_FAILED`
- `PROFILE_COMPOSITE_FAILED`
- existing `NO_PERSON`
- existing `MULTIPLE_PEOPLE`

Visitor mapping:
- engine unavailable → service/staff guidance
- quality failed → retake guidance
- timeout → retry guidance preserving name/team/mode

## 13. Performance Targets

These are **targets, not measured results**.

- ideal visitor wait: < 8 sec
- acceptable EXPO wait: < 15 sec
- current app operation timeout: 25 sec
- preview/detection path must stay responsive while camera is active

Measure on actual Pi / selected GPU machine before finalizing.

## 14. Privacy

- raw capture is memory-only where practical
- do not store face embedding for Mode B unless separately justified
- generated preview is temporary
- output lifecycle/retention must be defined before exhibition
- no browser-side secret/API key
- no external photo transmission under current product decision
- logs must not contain raw photo bytes

## 15. Test Matrix

Normal:
- one centered face
- glasses
- different clothing colors
- light/dark background
- taller/shorter user framing

Boundary:
- face near edge
- shoulder partly cut
- backlight
- low light
- slight head rotation

Failure:
- zero people
- multiple people
- engine unavailable
- timeout
- corrupt result
- session reset while job in flight

## 16. Implementation Order

1. define neutral suit transparent master
2. implement backend `ProfileEngine` interface
3. build LocalCVEngine
4. add `/api/profile/generate`
5. add live `generateProfile` adapter
6. test RESULT B end-to-end
7. benchmark real Pi
8. only then evaluate local GPU enhancement
