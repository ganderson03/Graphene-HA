/**
 * Task case 285: alias_hop_chain_08 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case285AliasHopChain08(input) {
  const taskName = 'alias_hop_chain_08';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const a = payload;
  const b = a;
  const c = b;
  // ESCAPE: multi-hop alias chain into retained sink.
  retainedAudit.push(c);
  return 'ok';
}

module.exports = { case285AliasHopChain08 };
