"""
Task case 002: cache order payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_002_cache_order(input_data):
    # Task: cache order records and prepare transport-ready payload.
    task_name = 'cache_order'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'order',
        'stage': 'cache',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is appended to RETAINED_AUDIT, outliving function scope.
    RETAINED_AUDIT.append(payload)
    return 'ok'
