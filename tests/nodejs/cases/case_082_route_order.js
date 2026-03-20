/**
 * Task case 082: route_order
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case082RouteOrder(input) {
  // Task: route order records and prepare transport-ready payload.
  const taskName = 'route_order';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'order',
    stage: 'route',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: payload is appended to retained audit state, outliving function scope.
  retainedAudit.push(payload);
  return 'ok';
}

module.exports = {
  case082RouteOrder,
};
