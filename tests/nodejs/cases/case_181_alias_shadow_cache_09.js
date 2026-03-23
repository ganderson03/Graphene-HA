/**
 * Task case 181: alias_shadow_cache_09 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case181AliasShadowCache09(input) {
  const taskName = 'alias_shadow_cache_09';
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
  retainedCache.set('case_181', alias);
  return 'ok';
}

module.exports = {
  case181AliasShadowCache09,
};
