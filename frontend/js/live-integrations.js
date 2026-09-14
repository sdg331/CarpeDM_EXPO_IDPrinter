// Implement these logical methods after the hardware/backend contract is agreed.
// No proposed REST path is assumed to exist. Keep IDs backend-owned.
// Pass { signal, operationId } through every implementation. A retry MUST reuse
// operationId; the server must deduplicate writes/prints and report final truth.
// registerNfc: ({ name, teamId, aiMode, result }, context)
//   -> { status: 'verified', sessionId }
// generateProfile: (frame, context) -> { image, kind: 'B' }
// issueBadge: (sessionId, context) -> { status: 'success' }
// resolveCheckout: (context) -> { sessionId, name, teamId }
// getMirrorTingReport: (sessionId, context) -> { status: 'available', ...report }
// printReport: (report, context) -> { status: 'success' }
export const liveIntegrations = Object.freeze({});
