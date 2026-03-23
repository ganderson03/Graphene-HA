"""
Task case 178: local_cache_named_retained_08 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_178_local_cache_named_retained_08(input_data):
    task_name = 'local_cache_named_retained_08'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    retained_cache_local = {}
    retained_cache_local['tmp'] = payload
    # SAFE: payload is only stored in local container that dies at return.
    return payload['checksum']
