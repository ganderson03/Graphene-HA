/**
 * Task case 180: closure_no_escape_08 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case180ClosureNoEscape08(input) {
  const taskName = 'closure_no_escape_08';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const consume = () => payload.task;
  void consume();
  // SAFE: closure invoked locally and not retained.
  return payload.checksum;
}

module.exports = {
  case180ClosureNoEscape08,
};
