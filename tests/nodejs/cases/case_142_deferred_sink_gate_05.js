/**
 * Task case 142: deferred_sink_gate_05 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case142DeferredSinkGate05(input) {
  const taskName = 'deferred_sink_gate_05';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  if (raw.startsWith('x')) {
    // ESCAPE: conditional sink only on selected path.
    retainedAudit.push(payload);
  }
  return 'ok';
}

module.exports = {
  case142DeferredSinkGate05,
};
