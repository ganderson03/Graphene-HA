/**
 * Task case 198: local_cache_named_retained_10 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case198LocalCacheNamedRetained10(input) {
  const taskName = 'local_cache_named_retained_10';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const retainedCacheLocal = new Map();
  retainedCacheLocal.set('tmp', payload);
  // SAFE: local map does not escape.
  return payload.checksum;
}

module.exports = {
  case198LocalCacheNamedRetained10,
};
