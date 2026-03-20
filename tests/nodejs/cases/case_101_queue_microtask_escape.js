/**
 * Paper-inspired case 101: scheduler-sensitive async escape.
 * Inspired by ThreadSanitizer-style dynamic limitations for schedule-dependent behavior.
 */

const retainedCase101Microtasks = [];

function case101QueueMicrotaskEscape(input) {
  const raw = input || 'sample';
  const payload = {
    task: 'queue_microtask_escape',
    entity: 'microtask',
    stage: 'deferred',
    input: raw,
  };

  // ESCAPE: payload escapes to asynchronous microtask after function return.
  queueMicrotask(() => {
    retainedCase101Microtasks.push(payload);
  });

  return 'queued';
}

module.exports = {
  case101QueueMicrotaskEscape,
};
