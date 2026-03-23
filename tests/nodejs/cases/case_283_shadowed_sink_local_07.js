/**
 * Task case 283: shadowed_sink_local_07 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case283ShadowedSinkLocal07(input) {
  const taskName = 'shadowed_sink_local_07';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const retainedCache = new Map();
  retainedCache.set('tmp', payload);
  // SAFE: local shadow hides global sink symbol.
  return payload.checksum;
}

module.exports = { case283ShadowedSinkLocal07 };
