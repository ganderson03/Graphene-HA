/**
 * Task case 126: decoy_retained_string_03 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case126DecoyRetainedString03(input) {
  const taskName = 'decoy_retained_string_03';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const marker = 'retainedCache literal only';
  void (marker + payload.task);
  // SAFE: no retained sink receives payload object.
  return payload.checksum;
}

module.exports = {
  case126DecoyRetainedString03,
};
