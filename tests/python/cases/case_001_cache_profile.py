"""
Task case 001: cache profile payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_001_cache_profile(input_data):
    # Task: cache profile records and prepare transport-ready payload.
    task_name = 'cache_profile'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'profile',
        'stage': 'cache',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is promoted to module-level RETAINED_CACHE for cross-request reuse.
    RETAINED_CACHE['case_001'] = payload
    return 'ok'
