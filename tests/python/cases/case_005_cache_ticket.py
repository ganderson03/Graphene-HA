"""
Task case 005: cache ticket payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_005_cache_ticket(input_data):
    # Task: cache ticket records and prepare transport-ready payload.
    task_name = 'cache_ticket'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'ticket',
        'stage': 'cache',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # SAFE: payload remains local; only primitive checksum string is returned.
    return payload['checksum']
