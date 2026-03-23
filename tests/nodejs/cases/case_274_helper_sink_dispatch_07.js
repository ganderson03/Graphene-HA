/**
 * Task case 274: helper_sink_dispatch_07 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case274HelperSinkDispatch07(input) {
  const taskName = 'helper_sink_dispatch_07';
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

module.exports = { case274HelperSinkDispatch07 };
