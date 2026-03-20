"""
Task case 044: normalize shipment payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_044_normalize_shipment(input_data):
    # Task: normalize shipment records and prepare transport-ready payload.
    task_name = 'normalize_shipment'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'shipment',
        'stage': 'normalize',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # ESCAPE: payload is nested inside retained envelope persisted to RETAINED_AUDIT.
    envelope = {'source': 'pipeline', 'payload': payload}
    RETAINED_AUDIT.append(envelope)
    return 'ok'
