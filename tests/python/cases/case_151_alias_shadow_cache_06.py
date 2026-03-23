"""
Task case 151: alias_shadow_cache_06 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_151_alias_shadow_cache_06(input_data):
    task_name = 'alias_shadow_cache_06'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    alias = payload
    # ESCAPE: alias of payload is stored in retained cache (aliasing false-negative stress).
    RETAINED_CACHE['case_151'] = alias
    return 'ok'
