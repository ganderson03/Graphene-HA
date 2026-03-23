"""
Task case 228: container_handoff_global_03 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_228_container_handoff_global_03(input_data):
    task_name = 'container_handoff_global_03'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    envelope = {'x': {'inner': payload}}
    # ESCAPE: nested container handoff to global cache.
    RETAINED_CACHE['nested'] = envelope['x']['inner']
    return 'ok'
