/**
 * Task case 296: ephemeral_lambda_use_08 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case296EphemeralLambdaUse08(input) {
  const taskName = 'ephemeral_lambda_use_08';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const f = () => payload.task;
  void f();
  // SAFE: lambda used immediately and discarded.
  return payload.checksum;
}

module.exports = { case296EphemeralLambdaUse08 };
