/**
 * Task case 062: enrich_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case062EnrichOrder(input) {
  // Task: enrich order records and prepare transport-ready payload.
  const taskName = 'enrich_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'enrich',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case062EnrichOrder,
};
