"""
Task case 245: local_clone_named_retained_04 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_245_local_clone_named_retained_04(input_data):
    task_name = 'local_clone_named_retained_04'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    retained_local = [dict(payload)]
    _ = retained_local[0]['task']
    # SAFE: misleading local name but no global retention.
    return payload['checksum']
