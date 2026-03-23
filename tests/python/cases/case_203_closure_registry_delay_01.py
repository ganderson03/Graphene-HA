"""
Task case 203: closure_registry_delay_01 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_203_closure_registry_delay_01(input_data):
    task_name = 'closure_registry_delay_01'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    def later() -> str:
        RETAINED_AUDIT.append(payload)
        return payload['input']
    # ESCAPE: retained closure mutates global sink when invoked later.
    RETAINED_HANDLERS.append(later)
    return 'ok'
