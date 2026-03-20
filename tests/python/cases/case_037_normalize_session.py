"""
Task case 037: normalize session payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_037_normalize_session(input_data):
    # Task: normalize session records and prepare transport-ready payload.
    task_name = 'normalize_session'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'session',
        'stage': 'normalize',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is appended to RETAINED_AUDIT, outliving function scope.
    RETAINED_AUDIT.append(payload)
    return 'ok'
