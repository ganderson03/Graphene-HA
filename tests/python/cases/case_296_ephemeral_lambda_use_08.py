"""
Task case 296: ephemeral_lambda_use_08 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_296_ephemeral_lambda_use_08(input_data):
    task_name = 'ephemeral_lambda_use_08'
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
