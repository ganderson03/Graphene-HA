/**
 * Task case 292: copy_then_drop_08 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case292CopyThenDrop08(input) {
  const taskName = 'copy_then_drop_08';
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

module.exports = { case292CopyThenDrop08 };
