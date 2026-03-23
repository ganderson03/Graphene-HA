/**
 * Task case 185: thread_handoff_late_09 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case185ThreadHandoffLate09(input) {
  const taskName = 'thread_handoff_late_09';
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
  case185ThreadHandoffLate09,
};
