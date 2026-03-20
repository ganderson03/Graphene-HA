"""
Task case 038: normalize inventory payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_038_normalize_inventory(input_data):
    # Task: normalize inventory records and prepare transport-ready payload.
    task_name = 'normalize_inventory'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'inventory',
        'stage': 'normalize',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: closure captures payload and handler is retained in RETAINED_HANDLERS.
    def handler():
        return payload['checksum']
    RETAINED_HANDLERS.append(handler)
    return 'ok'
