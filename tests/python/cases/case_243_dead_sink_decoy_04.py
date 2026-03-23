"""
Task case 243: dead_sink_decoy_04 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_243_dead_sink_decoy_04(input_data):
    task_name = 'dead_sink_decoy_04'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    if 2 + 2 == 5:
        RETAINED_AUDIT.append(payload)
    # SAFE: sink exists but dead arithmetic branch blocks execution.
    return payload['checksum']
