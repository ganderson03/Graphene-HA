"""
Task case 236: ephemeral_lambda_use_03 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_236_ephemeral_lambda_use_03(input_data):
    task_name = 'ephemeral_lambda_use_03'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    handler = lambda: payload['task']
    _ = handler()
    # SAFE: lambda consumed inline and never persisted.
    return payload['checksum']
