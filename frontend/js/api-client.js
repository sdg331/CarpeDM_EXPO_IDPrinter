import { liveIntegrations } from "./live-integrations.js";

export class KioskError extends Error {
  constructor(code, retryable = true) {
    super(code);
    this.code = code;
    this.retryable = retryable;
  }
}
export const errorCopy = {
  BACKEND_UNAVAILABLE: [
    "서비스에 연결하지 못했어요.",
    "잠시 후 다시 시도해주세요. 계속 연결되지 않으면 현장 스태프에게 알려주세요.",
  ],
  INTEGRATION_PENDING: [
    "아직 연결을 준비하고 있어요.",
    "이 기능은 장치와 서비스 연결 후 사용할 수 있어요. 현장 스태프에게 문의해주세요.",
  ],
  CAMERA_UNAVAILABLE: [
    "카메라를 사용할 수 없어요.",
    "카메라 연결과 브라우저 권한을 확인한 후 다시 시도해주세요.",
  ],
  NO_PERSON: [
    "얼굴을 찾지 못했어요.",
    "카메라 앞으로 조금 더 가까이 와서 다시 촬영해주세요.",
  ],
  MULTIPLE_PEOPLE: [
    "여러 명의 얼굴이 보여요.",
    "한 분만 화면 안에 들어와 다시 촬영해주세요.",
  ],
  AI_ERROR: [
    "분석하지 못했어요.",
    "입력한 정보는 그대로예요. 다시 촬영해주세요.",
  ],
  AI_TIMEOUT: [
    "결과 생성이 예상보다 오래 걸리고 있어요.",
    "입력한 정보는 그대로예요. 다시 촬영해주세요.",
  ],
  NFC_ERROR: [
    "카드에 정보를 등록하지 못했어요.",
    "카드를 리더에 가까이 대고 다시 시도해주세요.",
  ],
  NFC_TIMEOUT: ["카드를 확인하지 못했어요.", "카드를 다시 한 번 태그해주세요."],
  PRINTER_ERROR: [
    "프린터를 사용할 수 없어요.",
    "사원 정보는 그대로예요. 스태프의 안내에 따라 다시 시도해주세요.",
  ],
  UNKNOWN_CARD: [
    "등록되지 않은 카드예요.",
    "입사할 때 등록한 사원증인지 확인한 후 다시 태그해주세요.",
  ],
  UNKNOWN_OUTCOME: [
    "처리 결과를 확인하고 있어요.",
    "중복 등록이나 출력을 막기 위해 자동으로 다시 요청하지 않아요. 현장 스태프에게 확인해주세요.",
  ],
  INVALID_RESPONSE: [
    "결과를 확인하지 못했어요.",
    "현장 스태프에게 문의해주세요.",
  ],
};

export async function request(path, options = {}, fetcher = fetch) {
  const controller = new AbortController();
  const external = options.signal;
  const abort = () => controller.abort();
  external?.addEventListener("abort", abort, { once: true });
  if (external?.aborted) controller.abort();
  const timer = setTimeout(abort, options.timeout ?? 20000);
  try {
    const response = await fetcher(path, {
      ...options,
      signal: controller.signal,
    });
    if (!response.ok) throw new KioskError("BACKEND_UNAVAILABLE");
    return await response.json();
  } catch (error) {
    if (external?.aborted) throw new DOMException("Aborted", "AbortError");
    if (error instanceof KioskError) throw error;
    throw new KioskError(
      controller.signal.aborted ? "AI_TIMEOUT" : "BACKEND_UNAVAILABLE",
    );
  } finally {
    clearTimeout(timer);
    external?.removeEventListener("abort", abort);
  }
}

export function normalizeMatch(data) {
  if (!data.ok)
    throw new KioskError(
      { no_face: "NO_PERSON", multiple_faces: "MULTIPLE_PEOPLE" }[data.error] ||
        "AI_ERROR",
    );
  const character = data.characters?.[data.top];
  if (
    !Number.isInteger(data.top) ||
    !character ||
    !/^char_0[1-8]$/.test(character.id)
  )
    throw new KioskError("INVALID_RESPONSE", false);
  return {
    kind: "A",
    characterId: character.id,
    image: `/assets/characters/${character.id}.png`,
  };
}

const multipart = (frame) => {
  const form = new FormData();
  form.append("frame", frame, "capture.jpg");
  return form;
};
function wait(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted)
      return reject(new DOMException("Aborted", "AbortError"));
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", abort);
      resolve();
    }, ms);
    signal?.addEventListener("abort", abort, { once: true });
  });
}

// Deterministic fixtures are available ONLY through explicit ?demo=1.
// They never activate in response to a failed real service request.
export function createDemoApi(scenario = "success") {
  const attempts = new Set();
  const jobs = new Map();
  async function operation(name, context, result, failure) {
    const key = `${name}:${context.operationId}`;
    if (jobs.has(key)) return jobs.get(key);
    if (name === "nfc" || name === "checkout") {
      context.onStatus?.("detected");
      await wait(250, context.signal);
      context.onStatus?.(name === "nfc" ? "writing" : "resolving");
      await wait(350, context.signal);
      if (name === "nfc") context.onStatus?.("verifying");
    }
    if (name === "badge" || name === "reportPrint")
      context.onStatus?.("printing");
    await wait(scenario === "slow" ? 4300 : 950, context.signal);
    if (failure && !attempts.has(name)) {
      attempts.add(name);
      throw new KioskError(failure);
    }
    jobs.set(key, result);
    return result;
  }
  return {
    demo: true,
    scenario,
    reset() {
      attempts.clear();
      jobs.clear();
    },
    getHealth: async () => ({ ok: true }),
    detectPreview: async () => ({
      ok: scenario === "success",
      count:
        scenario === "no_person" ? 0 : scenario === "multiple_people" ? 2 : 1,
    }),
    matchCharacter: (_, ctx) =>
      operation(
        "ai",
        ctx,
        {
          kind: "A",
          characterId: "char_01",
          image: "/assets/characters/char_01.png",
        },
        scenario === "ai_error"
          ? "AI_ERROR"
          : scenario === "ai_timeout"
            ? "AI_TIMEOUT"
            : null,
      ),
    generateProfile: (_, ctx) =>
      operation(
        "ai",
        ctx,
        { kind: "B", image: "/assets/characters/char_02.png", sample: true },
        scenario === "ai_error"
          ? "AI_ERROR"
          : scenario === "ai_timeout"
            ? "AI_TIMEOUT"
            : null,
      ),
    registerNfc: (_, ctx) =>
      operation(
        "nfc",
        ctx,
        { status: "verified", sessionId: "DEMO-0001" },
        scenario === "nfc_error"
          ? "NFC_ERROR"
          : scenario === "nfc_timeout"
            ? "NFC_TIMEOUT"
            : null,
      ),
    issueBadge: (_, ctx) =>
      operation(
        "badge",
        ctx,
        { status: "success", demo: true },
        scenario === "printer_error" ? "PRINTER_ERROR" : null,
      ),
    resolveCheckout: (ctx) =>
      operation(
        "checkout",
        ctx,
        { sessionId: "DEMO-0002", name: "김미래", teamId: "design" },
        scenario === "unknown_card"
          ? "UNKNOWN_CARD"
          : scenario === "nfc_timeout"
            ? "NFC_TIMEOUT"
            : null,
      ),
    getMirrorTingReport: (sessionId, ctx) =>
      operation(
        "report",
        ctx,
        scenario === "no_report"
          ? { status: "not_found" }
          : {
              status: "available",
              sessionId,
              reportId: "DEMO-REPORT-0002",
              scenario: "새로운 팀원과 첫 미팅",
              summary:
                "팀원의 의견을 듣고, 자신의 생각을 차분하게 나누는 대화를 체험했어요.",
              strength: "상대방의 이야기에 귀 기울이는 태도",
              nextAction: "다음 대화에서는 열린 질문을 한 가지 더 건네보세요.",
              modeLabel: "AI 캐릭터 매칭",
              checkinAt: "2026.09.15 10:00",
              checkoutAt: "2026.09.15 10:15",
              sample: true,
            },
      ),
    printReport: (_, ctx) =>
      operation(
        "reportPrint",
        ctx,
        { status: "success", demo: true },
        scenario === "printer_error" ? "PRINTER_ERROR" : null,
      ),
  };
}

export function createLiveApi(
  integrations = liveIntegrations,
  fetcher = fetch,
) {
  const call = async (name, ...args) => {
    if (typeof integrations[name] !== "function")
      throw new KioskError("INTEGRATION_PENDING", false);
    // Unknown write outcomes must be reconciled by the service, not retried blindly.
    try {
      return await integrations[name](...args);
    } catch (error) {
      if (error instanceof KioskError || error.name === "AbortError")
        throw error;
      throw new KioskError("UNKNOWN_OUTCOME", false);
    }
  };
  return {
    demo: false,
    reset() {},
    getHealth: (signal) =>
      request("/api/health", { signal, timeout: 4000 }, fetcher),
    detectPreview: (frame, { signal } = {}) =>
      request(
        "/api/detect",
        { method: "POST", body: multipart(frame), signal, timeout: 5000 },
        fetcher,
      ),
    matchCharacter: async (frame, { signal } = {}) =>
      normalizeMatch(
        await request(
          "/api/match",
          { method: "POST", body: multipart(frame), signal },
          fetcher,
        ),
      ),
    generateProfile: (...args) => call("generateProfile", ...args),
    registerNfc: (...args) => call("registerNfc", ...args),
    issueBadge: (...args) => call("issueBadge", ...args),
    resolveCheckout: (...args) => call("resolveCheckout", ...args),
    getMirrorTingReport: (...args) => call("getMirrorTingReport", ...args),
    printReport: (...args) => call("printReport", ...args),
  };
}
