/**
 * Task case 140: closure_no_escape_04 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case140ClosureNoEscape04(input) {
  const taskName = 'closure_no_escape_04';
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
  case140ClosureNoEscape04,
};
