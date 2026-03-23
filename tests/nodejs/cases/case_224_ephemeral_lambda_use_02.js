/**
 * Task case 224: ephemeral_lambda_use_02 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case224EphemeralLambdaUse02(input) {
  const taskName = 'ephemeral_lambda_use_02';
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

module.exports = { case224EphemeralLambdaUse02 };
