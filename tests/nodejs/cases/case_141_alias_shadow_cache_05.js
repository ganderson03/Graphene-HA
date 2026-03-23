/**
 * Task case 141: alias_shadow_cache_05 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case141AliasShadowCache05(input) {
  const taskName = 'alias_shadow_cache_05';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const alias = payload;
  // ESCAPE: alias of payload is retained (aliasing false-negative stress).
  retainedCache.set('case_141', alias);
  return 'ok';
}

module.exports = {
  case141AliasShadowCache05,
};
