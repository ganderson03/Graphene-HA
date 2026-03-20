"""
Task case 021: stage profile payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_021_stage_profile(input_data):
    # Task: stage profile records and prepare transport-ready payload.
    task_name = 'stage_profile'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'profile',
        'stage': 'stage',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is promoted to module-level RETAINED_CACHE for cross-request reuse.
    RETAINED_CACHE['case_021'] = payload
    return 'ok'
