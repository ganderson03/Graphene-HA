"""
Task case 092: reconcile order payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_092_reconcile_order(input_data):
    # Task: reconcile order records and prepare transport-ready payload.
    task_name = 'reconcile_order'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'order',
        'stage': 'reconcile',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is appended to RETAINED_AUDIT, outliving function scope.
    RETAINED_AUDIT.append(payload)
    return 'ok'
