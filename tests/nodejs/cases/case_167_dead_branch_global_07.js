/**
 * Task case 167: dead_branch_global_07 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case167DeadBranchGlobal07(input) {
  const taskName = 'dead_branch_global_07';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  if (false) {
    retainedCache.set('case_167', payload);
  }
  // SAFE: sink is dead branch only.
  return payload.checksum;
}

module.exports = {
  case167DeadBranchGlobal07,
};
