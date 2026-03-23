"""
Task case 220: copy_then_drop_02 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_220_copy_then_drop_02(input_data):
    task_name = 'copy_then_drop_02'
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
