/**
 * Task case 124: indirect_container_write_03 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case124IndirectContainerWrite03(input) {
  const taskName = 'indirect_container_write_03';
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
  case124IndirectContainerWrite03,
};
