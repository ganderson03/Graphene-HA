/**
 * Task case 037: normalize_session
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case037NormalizeSession(input) {
  // Task: normalize session records and prepare transport-ready payload.
  const taskName = 'normalize_session';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'session',
    stage: 'normalize',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case037NormalizeSession,
};
