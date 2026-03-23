/**
 * Task case 240: container_handoff_global_04 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case240ContainerHandoffGlobal04(input) {
  const taskName = 'container_handoff_global_04';
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

module.exports = { case240ContainerHandoffGlobal04 };
