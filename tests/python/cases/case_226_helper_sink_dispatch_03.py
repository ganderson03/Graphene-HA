"""
Task case 226: helper_sink_dispatch_03 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_226_helper_sink_dispatch_03(input_data):
    task_name = 'helper_sink_dispatch_03'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    def sink(obj):
        RETAINED_AUDIT.append(obj)
    # ESCAPE: helper function dispatch hides sink call site.
    sink(payload)
    return 'ok'
