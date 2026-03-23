/**
 * Task case 216: container_handoff_global_02 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case216ContainerHandoffGlobal02(input) {
  const taskName = 'container_handoff_global_02';
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

module.exports = { case216ContainerHandoffGlobal02 };
