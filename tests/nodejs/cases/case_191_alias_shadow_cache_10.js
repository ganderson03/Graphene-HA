/**
 * Task case 191: alias_shadow_cache_10 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case191AliasShadowCache10(input) {
  const taskName = 'alias_shadow_cache_10';
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
  retainedCache.set('case_191', alias);
  return 'ok';
}

module.exports = {
  case191AliasShadowCache10,
};
