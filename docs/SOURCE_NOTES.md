# Source Notes

이 핸드오프 패키지는 다음을 결합해 정리했다.

1. 프로젝트 대화에서 확정된 MIRRORTING WORKS UX/하드웨어 결정
2. 업로드된 `CarpeDM_2026DMUEXPO_RaspberryPi-main.zip` 실제 코드 구조
3. 업로드된 `MIRRORTING WORKS 키오스크 프론트엔드 핸드오프·Figma 설계 연구 보고서.pdf`

중요한 정합성 수정:
- 연구 보고서의 일부 `TBD`(팀명 등)는 이후 대화에서 확정된 값으로 갱신했다.
- 현재 코드는 Vite/React가 아니라 vanilla HTML/CSS/JS이므로 전시 전 프레임워크 마이그레이션을 권장하지 않는다.
- 현재 카메라 preview는 browser `getUserMedia()`를 직접 사용하므로, 이를 CURRENT architecture로 명시하고 AI/NFC/print 경계와 구분했다.
- 현재 랜덤 캐릭터 폴백은 목표 제품에서 금지한다.

문서의 CURRENT/CONFIRMED/PROPOSED/TBD 표기를 구분해 사용한다.
