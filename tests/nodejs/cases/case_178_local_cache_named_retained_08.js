/**
 * Task case 178: local_cache_named_retained_08 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case178LocalCacheNamedRetained08(input) {
  const taskName = 'local_cache_named_retained_08';
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
  case178LocalCacheNamedRetained08,
};
