"""
Task case 096:  subscription payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_096__subscription(input_data):
    # Task:  subscription records and prepare transport-ready payload.
    task_name = '_subscription'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'subscription',
        'stage': '',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is promoted to module-level RETAINED_CACHE for cross-request reuse.
    RETAINED_CACHE['case_096'] = payload
    return 'ok'
