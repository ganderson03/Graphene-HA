/**
 * Task case 267: dead_sink_decoy_06 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case267DeadSinkDecoy06(input) {
  const taskName = 'dead_sink_decoy_06';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  if (1 === 2) { retainedAudit.push(payload); }
  // SAFE: dead branch only.
  return payload.checksum;
}

module.exports = { case267DeadSinkDecoy06 };
