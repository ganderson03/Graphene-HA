/**
 * Task case 225: alias_hop_chain_03 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case225AliasHopChain03(input) {
  const taskName = 'alias_hop_chain_03';
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

module.exports = { case225AliasHopChain03 };
