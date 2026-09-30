// Live backend integrations for the hardware paths that have an implemented
// server contract. Mode B and MirrorTing report APIs intentionally remain absent
// until their backend contracts are verified.

const errorMap = {
  NFC_READER_OFFLINE: "NFC_ERROR",
  NFC_READ_FAILED: "NFC_ERROR",
  BADGE_RENDER_FAILED: "PRINTER_ERROR",
  SESSION_NOT_FOUND: "INVALID_RESPONSE",
  BADGE_DATA_INCOMPLETE: "INVALID_RESPONSE",
  INVALID_AI_RESULT: "INVALID_RESPONSE",
  INVALID_TEAM: "INVALID_RESPONSE",
  SESSION_CREATE_FAILED: "BACKEND_UNAVAILABLE",
  OPERATION_CONFLICT: "UNKNOWN_OUTCOME",
  MODE_B_NOT_READY: "INTEGRATION_PENDING",
};

async function postJson(path, payload, context) {
  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      signal: context.signal,
    });
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

export const liveIntegrations = Object.freeze({
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
    );
  },

  resolveCheckout(context) {
    return postJson(
      "/api/nfc/resolve",
      { operationId: context.operationId },
      context,
    );
  },
});
