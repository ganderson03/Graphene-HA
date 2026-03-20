/**
 * Task case 072: snapshot_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case072SnapshotOrder(input) {
  // Task: snapshot order records and prepare transport-ready payload.
  const taskName = 'snapshot_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'snapshot',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case072SnapshotOrder,
};
