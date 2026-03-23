"""
Task case 176: decoy_retained_string_08 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_176_decoy_retained_string_08(input_data):
    task_name = 'decoy_retained_string_08'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    marker = 'RETAINED_CACHE is only a string marker, not a sink'
    _ = marker + payload['task']
    # SAFE: no object escapes local scope; only primitive output leaves.
    return payload['checksum']
