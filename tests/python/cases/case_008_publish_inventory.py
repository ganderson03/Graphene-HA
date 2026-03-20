"""
Task case 008: publish inventory payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_008_publish_inventory(input_data):
    # Task: publish inventory records and prepare transport-ready payload.
    task_name = 'publish_inventory'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'inventory',
        'stage': 'publish',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: closure captures payload and handler is retained in RETAINED_HANDLERS.
    def handler():
        return payload['checksum']
    RETAINED_HANDLERS.append(handler)
    return 'ok'
