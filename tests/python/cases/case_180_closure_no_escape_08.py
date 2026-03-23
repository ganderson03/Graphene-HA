"""
Task case 180: closure_no_escape_08 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_180_closure_no_escape_08(input_data):
    task_name = 'closure_no_escape_08'
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
