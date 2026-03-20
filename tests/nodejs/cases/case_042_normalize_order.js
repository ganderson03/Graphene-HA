/**
 * Task case 042: normalize_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case042NormalizeOrder(input) {
  // Task: normalize order records and prepare transport-ready payload.
  const taskName = 'normalize_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'normalize',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case042NormalizeOrder,
};
