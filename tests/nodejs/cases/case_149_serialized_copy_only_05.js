/**
 * Task case 149: serialized_copy_only_05 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case149SerializedCopyOnly05(input) {
  const taskName = 'serialized_copy_only_05';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const serialized = JSON.stringify(payload);
  // SAFE: only primitive serialized data leaves scope.
  return serialized;
}

module.exports = {
  case149SerializedCopyOnly05,
};
