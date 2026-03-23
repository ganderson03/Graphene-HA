/**
 * Task case 290: thread_pool_capture_08 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case290ThreadPoolCapture08(input) {
  const taskName = 'thread_pool_capture_08';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: async task captures payload.
  setTimeout(() => retainedAudit.push(payload), 0);
  return 'ok';
}

module.exports = { case290ThreadPoolCapture08 };
