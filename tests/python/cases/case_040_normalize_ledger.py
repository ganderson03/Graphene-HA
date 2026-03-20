"""
Task case 040: normalize ledger payload for downstream business processing.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_040_normalize_ledger(input_data):
    # Task: normalize ledger records and prepare transport-ready payload.
    task_name = 'normalize_ledger'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'ledger',
        'stage': 'normalize',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    # SAFE: payload remains local; only primitive checksum string is returned.
    return payload['checksum']
