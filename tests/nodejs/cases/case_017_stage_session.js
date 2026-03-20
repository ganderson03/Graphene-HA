/**
 * Task case 017: stage_session
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case017StageSession(input) {
  // Task: stage session records and prepare transport-ready payload.
  const taskName = 'stage_session';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'session',
    stage: 'stage',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case017StageSession,
};
