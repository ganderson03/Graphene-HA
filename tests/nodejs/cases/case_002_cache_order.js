/**
 * Task case 002: cache_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case002CacheOrder(input) {
  // Task: cache order records and prepare transport-ready payload.
  const taskName = 'cache_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'cache',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case002CacheOrder,
};
