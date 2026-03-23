"""
Task case 169: serialized_copy_only_07 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_169_serialized_copy_only_07(input_data):
    task_name = 'serialized_copy_only_07'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    import json
    serialized = json.dumps(payload)
    # SAFE: only serialized primitive string leaves, payload object does not escape.
    return serialized
