"""
Task case 004: cache shipment payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_004_cache_shipment(input_data):
    # Task: cache shipment records and prepare transport-ready payload.
    task_name = 'cache_shipment'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'shipment',
        'stage': 'cache',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is nested inside retained envelope persisted to RETAINED_AUDIT.
    envelope = {'source': 'pipeline', 'payload': payload}
    RETAINED_AUDIT.append(envelope)
    return 'ok'
