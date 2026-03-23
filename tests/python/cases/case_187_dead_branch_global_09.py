"""
Task case 187: dead_branch_global_09 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_187_dead_branch_global_09(input_data):
    task_name = 'dead_branch_global_09'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    if False:
        RETAINED_CACHE['case_187'] = payload
    # SAFE: sink exists only in dead branch and never executes.
    return payload['checksum']
