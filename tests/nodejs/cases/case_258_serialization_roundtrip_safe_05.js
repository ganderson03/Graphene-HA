/**
 * Task case 258: serialization_roundtrip_safe_05 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case258SerializationRoundtripSafe05(input) {
  const taskName = 'serialization_roundtrip_safe_05';
  const raw = input || 'sample';
  const payload = {
    task: taskName,
    entity: 'extreme',
    stage: 'stress',
    input: raw,
    checksum: `${taskName}:${raw.length}`,
  };
  const roundtrip = JSON.parse(JSON.stringify(payload));
  void roundtrip.task;
  // SAFE: roundtrip object remains local.
  return payload.checksum;
}

module.exports = { case258SerializationRoundtripSafe05 };
