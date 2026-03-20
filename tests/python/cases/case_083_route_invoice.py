"""
Task case 083: route invoice payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_083_route_invoice(input_data):
    # Task: route invoice records and prepare transport-ready payload.
    task_name = 'route_invoice'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'invoice',
        'stage': 'route',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: closure captures payload and handler is retained in RETAINED_HANDLERS.
    def handler():
        return payload['checksum']
    RETAINED_HANDLERS.append(handler)
    return 'ok'
