/**
 * Task case 241: interface_sink_bridge_04 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case241InterfaceSinkBridge04(input) {
  const taskName = 'interface_sink_bridge_04';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const sink = { put(obj) { retainedAudit.push(obj); } };
  // ESCAPE: object method bridge to retained sink.
  sink.put(payload);
  return 'ok';
}

module.exports = { case241InterfaceSinkBridge04 };
