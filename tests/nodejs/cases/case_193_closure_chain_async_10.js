/**
 * Task case 193: closure_chain_async_10 false-positive/false-negative stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case193ClosureChainAsync10(input) {
  const taskName = 'closure_chain_async_10';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'stress',
    stage: 'evaluation',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const handler = () => payload.input;
  // ESCAPE: retained closure captures payload.
  retainedHandlers.push(handler);
  return 'ok';
}

module.exports = {
  case193ClosureChainAsync10,
};
