/**
 * Task case 288: container_handoff_global_08 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case288ContainerHandoffGlobal08(input) {
  const taskName = 'container_handoff_global_08';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const box = { deep: { value: payload } };
  // ESCAPE: nested indirection retained globally.
  retainedCache.set('nested', box.deep.value);
  return 'ok';
}

module.exports = { case288ContainerHandoffGlobal08 };
