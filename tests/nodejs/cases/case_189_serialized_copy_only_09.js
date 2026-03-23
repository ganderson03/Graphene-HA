/**
 * Task case 189: serialized_copy_only_09 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case189SerializedCopyOnly09(input) {
  const taskName = 'serialized_copy_only_09';
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
  case189SerializedCopyOnly09,
};
