// Keep NFC, printing, and session mutation behind the same-origin backend.
// Each hardware write uses a stable operationId supplied by app.js.

const errorMap = {
  NFC_READER_OFFLINE: "NFC_READER_OFFLINE",
  NFC_READ_FAILED: "NFC_ERROR",
  BADGE_RENDER_FAILED: "BADGE_RENDER_FAILED",
  SESSION_NOT_FOUND: "INVALID_RESPONSE",
  BADGE_DATA_INCOMPLETE: "INVALID_RESPONSE",
  INVALID_AI_RESULT: "INVALID_RESPONSE",
  INVALID_TEAM: "INVALID_RESPONSE",
  SESSION_CREATE_FAILED: "BACKEND_UNAVAILABLE",
  OPERATION_CONFLICT: "UNKNOWN_OUTCOME",
  MODE_B_NOT_READY: "INTEGRATION_PENDING",
};

async function postJson(path, payload, context, sideEffect = true, fetcher = fetch) {
  let response;
  try {
    response = await fetcher(path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      signal: context.signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    const code = sideEffect ? "UNKNOWN_OUTCOME" : "BACKEND_UNAVAILABLE";
    const wrapped = new Error(code);
    wrapped.code = code;
    wrapped.retryable = !sideEffect;
    throw wrapped;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    const error = new Error("INVALID_RESPONSE");
    error.code = "INVALID_RESPONSE";
    error.retryable = false;
    throw error;
  }

  if (!response.ok || data?.ok === false) {
    const backend = data?.error || {};
    const code = errorMap[backend.code] || backend.code || "BACKEND_UNAVAILABLE";
    const error = new Error(code);
    error.code = code;
    error.retryable = Boolean(backend.retryable);
    throw error;
  }
  return data;
}

async function getJson(path, context, fetcher = fetch) {
  let response;
  try {
    response = await fetcher(path, { signal: context.signal, cache: "no-store" });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    const wrapped = new Error("BACKEND_UNAVAILABLE");
    wrapped.code = "BACKEND_UNAVAILABLE";
    wrapped.retryable = true;
    throw wrapped;
  }
  let data;
  try {
    data = await response.json();
  } catch {
    const error = new Error("INVALID_RESPONSE");
    error.code = "INVALID_RESPONSE";
    error.retryable = false;
    throw error;
  }
  if (!response.ok || data?.ok === false) {
    const backend = data?.error || {};
    const code = errorMap[backend.code] || backend.code || "BACKEND_UNAVAILABLE";
    const error = new Error(code);
    error.code = code;
    error.retryable = Boolean(backend.retryable);
    throw error;
  }
  return data;
}

export function createLiveIntegrations(fetcher = fetch) {
  return Object.freeze({
  registerNfc(profile, context) {
    return postJson(
      "/api/nfc/register",
      {
        operationId: context.operationId,
        name: profile.name,
        teamId: profile.teamId,
        aiMode: profile.aiMode,
        result: profile.result,
      },
      context,
      true,
      fetcher,
    );
  },

  issueBadge(sessionId, context) {
    return postJson(
      "/api/badge/print",
      {
        operationId: context.operationId,
        sessionId,
      },
      context,
      true,
      fetcher,
    );
  },

  resolveCheckout(context) {
    return postJson(
      "/api/nfc/resolve",
      { operationId: context.operationId },
      context,
      false,
      fetcher,
    );
  },

  updateSessionProfile(sessionId, profileId, context) {
    return postJson(
      `/api/sessions/${encodeURIComponent(sessionId)}/profile`,
      { profileId },
      context,
      false,
      fetcher,
    );
  },

  getMirrorTingReport(sessionId, context) {
    return getJson(`/api/reports/${encodeURIComponent(sessionId)}`, context, fetcher);
  },

  printReport(report, context) {
    return postJson(
      "/api/reports/print",
      { operationId: context.operationId, sessionId: report.sessionId, reportId: report.reportId },
      context,
      true,
      fetcher,
    );
  },
  });
}

export const liveIntegrations = createLiveIntegrations();
