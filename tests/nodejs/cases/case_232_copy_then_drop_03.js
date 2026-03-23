/**
 * Task case 232: copy_then_drop_03 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case232CopyThenDrop03(input) {
  const taskName = 'copy_then_drop_03';
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

module.exports = { case232CopyThenDrop03 };
