/**
 * Task case 155: thread_handoff_late_06 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case155ThreadHandoffLate06(input) {
  const taskName = 'thread_handoff_late_06';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: async microtask captures payload beyond return edge.
  queueMicrotask(() => retainedAudit.push(payload));
  return 'ok';
}

module.exports = {
  case155ThreadHandoffLate06,
};
