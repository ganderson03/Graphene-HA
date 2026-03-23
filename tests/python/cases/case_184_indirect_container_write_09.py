"""
Task case 184: indirect_container_write_09 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_184_indirect_container_write_09(input_data):
    task_name = 'indirect_container_write_09'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    envelope = {'wrapped': payload}
    # ESCAPE: payload is indirectly persisted through nested container indirection.
    RETAINED_AUDIT.append(envelope['wrapped'])
    return 'ok'
