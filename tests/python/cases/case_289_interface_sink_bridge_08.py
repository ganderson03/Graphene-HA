"""
Task case 289: interface_sink_bridge_08 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_289_interface_sink_bridge_08(input_data):
    task_name = 'interface_sink_bridge_08'
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
