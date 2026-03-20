"""
Task case 062: enrich order payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_062_enrich_order(input_data):
    # Task: enrich order records and prepare transport-ready payload.
    task_name = 'enrich_order'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'order',
        'stage': 'enrich',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is appended to RETAINED_AUDIT, outliving function scope.
    RETAINED_AUDIT.append(payload)
    return 'ok'
