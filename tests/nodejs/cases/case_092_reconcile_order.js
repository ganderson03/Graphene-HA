/**
 * Task case 092: reconcile_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case092ReconcileOrder(input) {
  // Task: reconcile order records and prepare transport-ready payload.
  const taskName = 'reconcile_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'reconcile',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case092ReconcileOrder,
};
