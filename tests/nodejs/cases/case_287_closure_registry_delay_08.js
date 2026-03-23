/**
 * Task case 287: closure_registry_delay_08 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case287ClosureRegistryDelay08(input) {
  const taskName = 'closure_registry_delay_08';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const later = () => { retainedAudit.push(payload); return payload.input; };
  // ESCAPE: retained closure executes after caller returns.
  retainedHandlers.push(later);
  return 'ok';
}

module.exports = { case287ClosureRegistryDelay08 };
