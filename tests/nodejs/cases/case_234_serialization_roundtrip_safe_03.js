/**
 * Task case 234: serialization_roundtrip_safe_03 deep stress pattern.
 */

const retainedCache = new Map();
const retainedAudit = [];
const retainedHandlers = [];

function case234SerializationRoundtripSafe03(input) {
  const taskName = 'serialization_roundtrip_safe_03';
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

module.exports = { case234SerializationRoundtripSafe03 };
