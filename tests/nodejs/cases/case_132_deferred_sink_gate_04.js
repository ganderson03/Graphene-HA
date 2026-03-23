/**
 * Task case 132: deferred_sink_gate_04 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case132DeferredSinkGate04(input) {
  const taskName = 'deferred_sink_gate_04';
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
  case132DeferredSinkGate04,
};
