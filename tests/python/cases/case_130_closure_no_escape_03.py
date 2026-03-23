"""
Task case 130: closure_no_escape_03 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_130_closure_no_escape_03(input_data):
    task_name = 'closure_no_escape_03'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    def consume() -> str:
        return payload['task']
    _ = consume()
    # SAFE: closure is invoked locally and never retained.
    return payload['checksum']
