/**
 * Task case 264: container_handoff_global_06 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case264ContainerHandoffGlobal06(input) {
  const taskName = 'container_handoff_global_06';
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

module.exports = { case264ContainerHandoffGlobal06 };
