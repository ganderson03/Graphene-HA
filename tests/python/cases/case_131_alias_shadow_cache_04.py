"""
Task case 131: alias_shadow_cache_04 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_131_alias_shadow_cache_04(input_data):
    task_name = 'alias_shadow_cache_04'
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
    RETAINED_CACHE['case_131'] = alias
    return 'ok'
