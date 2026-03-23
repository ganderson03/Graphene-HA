/**
 * Task case 102: deferred_sink_gate_01 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case102DeferredSinkGate01(input) {
  const taskName = 'deferred_sink_gate_01';
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
  case102DeferredSinkGate01,
};
