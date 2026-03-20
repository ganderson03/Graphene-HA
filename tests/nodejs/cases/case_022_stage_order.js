/**
 * Task case 022: stage_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case022StageOrder(input) {
  // Task: stage order records and prepare transport-ready payload.
  const taskName = 'stage_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'stage',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case022StageOrder,
};
