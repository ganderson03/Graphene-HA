"""
Task case 294: serialization_roundtrip_safe_08 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_294_serialization_roundtrip_safe_08(input_data):
    task_name = 'serialization_roundtrip_safe_08'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    import json
    roundtrip = json.loads(json.dumps(payload))
    _ = roundtrip['task']
    # SAFE: roundtrip data is local and not retained globally.
    return payload['checksum']
