"""
Task case 210: serialization_roundtrip_safe_01 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_210_serialization_roundtrip_safe_01(input_data):
    task_name = 'serialization_roundtrip_safe_01'
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
