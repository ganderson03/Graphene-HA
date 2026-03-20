"""
Task case 078: route inventory payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_078_route_inventory(input_data):
    # Task: route inventory records and prepare transport-ready payload.
    task_name = 'route_inventory'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'inventory',
        'stage': 'route',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: closure captures payload and handler is retained in RETAINED_HANDLERS.
    def handler():
        return payload['checksum']
    RETAINED_HANDLERS.append(handler)
    return 'ok'
