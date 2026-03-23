/**
 * Task case 244: copy_then_drop_04 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case244CopyThenDrop04(input) {
  const taskName = 'copy_then_drop_04';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const copy = { ...payload };
  void copy.task;
  // SAFE: local copy never retained globally.
  return payload.checksum;
}

module.exports = { case244CopyThenDrop04 };
