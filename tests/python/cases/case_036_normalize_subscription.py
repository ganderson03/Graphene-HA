"""
Task case 036: normalize subscription payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_036_normalize_subscription(input_data):
    # Task: normalize subscription records and prepare transport-ready payload.
    task_name = 'normalize_subscription'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'subscription',
        'stage': 'normalize',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is promoted to module-level RETAINED_CACHE for cross-request reuse.
    RETAINED_CACHE['case_036'] = payload
    return 'ok'
