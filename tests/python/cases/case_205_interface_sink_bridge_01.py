"""
Task case 205: interface_sink_bridge_01 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_205_interface_sink_bridge_01(input_data):
    task_name = 'interface_sink_bridge_01'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    class Sink:
        def put(self, obj):
            RETAINED_AUDIT.append(obj)
    # ESCAPE: interface-like method bridge stores payload globally.
    Sink().put(payload)
    return 'ok'
