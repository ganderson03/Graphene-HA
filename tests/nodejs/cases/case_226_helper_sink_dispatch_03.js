/**
 * Task case 226: helper_sink_dispatch_03 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case226HelperSinkDispatch03(input) {
  const taskName = 'helper_sink_dispatch_03';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const sink = (obj) => retainedCache.set('helper', obj);
  // ESCAPE: helper function obscures sink dispatch.
  sink(payload);
  return 'ok';
}

module.exports = { case226HelperSinkDispatch03 };
