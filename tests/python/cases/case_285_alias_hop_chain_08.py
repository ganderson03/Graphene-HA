"""
Task case 285: alias_hop_chain_08 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_285_alias_hop_chain_08(input_data):
    task_name = 'alias_hop_chain_08'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    first = payload
    second = first
    third = second
    # ESCAPE: multi-hop alias chain ends in retained sink.
    RETAINED_CACHE['hop'] = third
    return 'ok'
