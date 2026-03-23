"""
Task case 110: closure_no_escape_01 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_110_closure_no_escape_01(input_data):
    task_name = 'closure_no_escape_01'
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
