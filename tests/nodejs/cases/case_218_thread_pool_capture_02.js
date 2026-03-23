/**
 * Task case 218: thread_pool_capture_02 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case218ThreadPoolCapture02(input) {
  const taskName = 'thread_pool_capture_02';
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

module.exports = { case218ThreadPoolCapture02 };
