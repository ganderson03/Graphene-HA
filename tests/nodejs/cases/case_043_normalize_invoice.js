/**
 * Task case 043: normalize_invoice
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case043NormalizeInvoice(input) {
  // Task: normalize invoice records and prepare transport-ready payload.
  const taskName = 'normalize_invoice';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'invoice',
    stage: 'normalize',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  // ESCAPE: closure captures payload and handler is retained in module-level handlers.
  retainedHandlers.push(() => payload.checksum);
  return 'ok';
}

module.exports = {
  case043NormalizeInvoice,
};
