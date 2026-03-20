/**
 * Task case 003: cache_invoice
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case003CacheInvoice(input) {
  // Task: cache invoice records and prepare transport-ready payload.
  const taskName = 'cache_invoice';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'invoice',
    stage: 'cache',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: closure captures payload and handler is retained in module-level handlers.
  retainedHandlers.push(() => payload.checksum);
  return 'ok';
}

module.exports = {
  case003CacheInvoice,
};
