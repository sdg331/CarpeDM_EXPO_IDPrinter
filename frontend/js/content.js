export const teams = [
  {
    id: "development",
    title: "개발팀",
    english: "Development",
    icon: "code",
    description:
      "아이디어를 실제로 사용할 수 있는 서비스와 기능으로 구현하는 팀입니다.",
    tasks: ["웹·앱 개발", "기능 구현", "시스템 유지보수"],
    keywords: ["개발", "서비스", "기술"],
  },
  {
    id: "ai",
    title: "AI팀",
    english: "Artificial Intelligence",
    icon: "spark",
    description:
      "데이터와 AI 기술을 활용해 새로운 기능과 서비스를 만드는 팀입니다.",
    tasks: ["AI 모델 개발", "데이터 분석", "모델 성능 개선"],
    keywords: ["AI", "데이터", "모델"],
  },
  {
    id: "design",
    title: "디자인팀",
    english: "Design",
    icon: "pen",
    description:
      "사용자가 쉽고 편하게 사용할 수 있는 화면과 경험을 설계합니다.",
    tasks: ["UI·UX 디자인", "그래픽 제작", "브랜드 디자인"],
    keywords: ["UIUX", "그래픽", "디자인"],
  },
  {
    id: "planning",
    title: "기획팀",
    english: "Product Planning",
    icon: "grid",
    description:
      "사용자의 문제를 발견하고 어떤 서비스를 만들지 설계하는 팀입니다.",
    tasks: ["서비스 기획", "기능 설계", "사용자 조사"],
    keywords: ["기획", "아이디어", "서비스"],
  },
  {
    id: "marketing",
    title: "마케팅팀",
    english: "Marketing",
    icon: "megaphone",
    description: "서비스의 매력을 알리고 더 많은 사람과 연결하는 팀입니다.",
    tasks: ["콘텐츠 제작", "홍보 캠페인", "브랜드 운영"],
    keywords: ["마케팅", "콘텐츠", "브랜드"],
  },
  {
    id: "hr",
    title: "인사팀",
    english: "People & Culture",
    icon: "people",
    description:
      "좋은 인재를 찾고 구성원이 함께 성장할 수 있는 환경을 만드는 팀입니다.",
    tasks: ["채용", "구성원 관리", "조직문화 운영"],
    keywords: ["채용", "조직", "문화"],
  },
];
export const modes = {
  A: {
    title: "AI 캐릭터 매칭",
    summary: "얼굴 특징을 분석해 가장 가까운 캐릭터를 찾아요.",
    detail:
      "AI가 얼굴의 특징을 분석해 8명의 MIRRORTING WORKS 캐릭터 중 가장 가까운 캐릭터를 찾아드립니다.",
    cta: "캐릭터 매칭 시작하기",
    steps: [
      ["사람 탐지", "카메라 앞 사용자를 찾습니다."],
      ["얼굴 분석", "얼굴 위치와 촬영 상태를 확인합니다."],
      ["특징 추출", "얼굴 특징을 128차원 데이터로 변환합니다."],
      ["캐릭터 비교", "8개 캐릭터의 특징과 비교합니다."],
      ["최종 매칭", "가장 가까운 캐릭터를 선택합니다."],
    ],
  },
  B: {
    title: "AI 프로필 생성",
    summary: "나만의 사원증 프로필을 만들어요.",
    detail:
      "촬영한 얼굴은 그대로 유지하면서 컴퓨터 비전 기술로 사원증용 프로필 사진을 만들어드립니다.",
    cta: "AI 프로필 만들기",
    steps: [
      ["사람·얼굴 탐지", "카메라 속 인물과 얼굴을 찾습니다."],
      ["자세 분석", "얼굴과 어깨의 위치를 확인합니다."],
      ["인물 분리", "인물과 배경을 구분합니다."],
      ["정장 합성", "포멀한 정장 이미지를 위치에 맞게 합성합니다."],
      ["프로필 완성", "배경과 구도를 정리하고 품질을 확인합니다."],
    ],
  },
};
export const scenarios = [
  ["success", "정상 흐름"],
  ["slow", "처리 지연"],
  ["camera_error", "카메라 연결 실패"],
  ["no_person", "얼굴 없음"],
  ["multiple_people", "여러 명 감지"],
  ["ai_error", "AI 분석 실패 후 재시도"],
  ["ai_timeout", "AI 시간 초과 후 재시도"],
  ["nfc_error", "NFC 등록 실패 후 재시도"],
  ["nfc_timeout", "NFC 시간 초과 후 재시도"],
  ["printer_error", "프린터 오류 후 재시도"],
  ["unknown_card", "등록되지 않은 카드"],
  ["no_report", "체험 기록 없음"],
  ["fatal", "서비스 점검 화면"],
];
export const screenIds = {
  home: "SCR-01",
  teams: "SCR-02",
  team: "SCR-03",
  name: "SCR-04",
  modes: "SCR-05",
  detailA: "SCR-06",
  detailB: "SCR-07",
  camera: "SCR-08",
  processing: "SCR-09",
  resultA: "SCR-10",
  resultB: "SCR-11",
  nfc: "SCR-12",
  badge: "SCR-13",
  checkinComplete: "SCR-14",
  checkout: "SCR-15",
  checkoutResult: "SCR-16",
  report: "SCR-17",
  reportPrint: "SCR-18",
  checkoutComplete: "SCR-19",
  fatal: "SCR-20",
};
