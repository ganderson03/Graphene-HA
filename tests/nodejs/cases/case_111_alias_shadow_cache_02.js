/**
 * Task case 111: alias_shadow_cache_02 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case111AliasShadowCache02(input) {
  const taskName = 'alias_shadow_cache_02';
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
  retainedCache.set('case_111', alias);
  return 'ok';
}

module.exports = {
  case111AliasShadowCache02,
};
