"""
Task case 133: closure_chain_async_04 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_133_closure_chain_async_04(input_data):
    task_name = 'closure_chain_async_04'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    def handler() -> str:
        return payload['input']
    # ESCAPE: closure captures payload and retained handler outlives function scope.
    RETAINED_HANDLERS.append(handler)
    return 'ok'
