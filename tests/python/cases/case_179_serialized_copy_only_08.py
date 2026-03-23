"""
Task case 179: serialized_copy_only_08 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_179_serialized_copy_only_08(input_data):
    task_name = 'serialized_copy_only_08'
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
