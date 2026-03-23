"""
Task case 248: ephemeral_lambda_use_04 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_248_ephemeral_lambda_use_04(input_data):
    task_name = 'ephemeral_lambda_use_04'
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
