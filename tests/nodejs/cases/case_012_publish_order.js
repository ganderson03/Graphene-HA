/**
 * Task case 012: publish_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case012PublishOrder(input) {
  // Task: publish order records and prepare transport-ready payload.
  const taskName = 'publish_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'publish',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case012PublishOrder,
};
