"""
Task case 157: dead_branch_global_06 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_157_dead_branch_global_06(input_data):
    task_name = 'dead_branch_global_06'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    if False:
        RETAINED_CACHE['case_157'] = payload
    # SAFE: sink exists only in dead branch and never executes.
    return payload['checksum']
