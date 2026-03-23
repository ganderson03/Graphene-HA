"""
Task case 271: shadowed_sink_local_06 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_271_shadowed_sink_local_06(input_data):
    task_name = 'shadowed_sink_local_06'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    RETAINED_CACHE = {}
    RETAINED_CACHE['tmp'] = payload
    # SAFE: shadowed local variable hides global sink symbol.
    return payload['checksum']
