/**
 * Task case 184: indirect_container_write_09 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case184IndirectContainerWrite09(input) {
  const taskName = 'indirect_container_write_09';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const envelope = { wrapped: payload };
  // ESCAPE: payload stored via indirection into retained sink.
  retainedAudit.push(envelope.wrapped);
  return 'ok';
}

module.exports = {
  case184IndirectContainerWrite09,
};
