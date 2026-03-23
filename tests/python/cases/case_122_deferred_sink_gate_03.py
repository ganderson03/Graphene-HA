"""
Task case 122: deferred_sink_gate_03 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_122_deferred_sink_gate_03(input_data):
    task_name = 'deferred_sink_gate_03'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    if raw.startswith('x'):
        # ESCAPE: conditional sink persists payload only on specific branch.
        RETAINED_AUDIT.append(payload)
    return 'ok'
