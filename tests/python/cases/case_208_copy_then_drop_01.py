"""
Task case 208: copy_then_drop_01 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_208_copy_then_drop_01(input_data):
    task_name = 'copy_then_drop_01'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    clone = dict(payload)
    _ = clone['task']
    # SAFE: clone stays local and is dropped at return.
    return payload['checksum']
