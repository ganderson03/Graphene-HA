"""
Task case 041: normalize profile payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_041_normalize_profile(input_data):
    # Task: normalize profile records and prepare transport-ready payload.
    task_name = 'normalize_profile'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'profile',
        'stage': 'normalize',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is promoted to module-level RETAINED_CACHE for cross-request reuse.
    RETAINED_CACHE['case_041'] = payload
    return 'ok'
