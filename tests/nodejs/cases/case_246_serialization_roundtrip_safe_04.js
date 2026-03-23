/**
 * Task case 246: serialization_roundtrip_safe_04 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case246SerializationRoundtripSafe04(input) {
  const taskName = 'serialization_roundtrip_safe_04';
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

module.exports = { case246SerializationRoundtripSafe04 };
