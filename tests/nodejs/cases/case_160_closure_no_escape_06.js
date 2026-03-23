/**
 * Task case 160: closure_no_escape_06 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case160ClosureNoEscape06(input) {
  const taskName = 'closure_no_escape_06';
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
  case160ClosureNoEscape06,
};
