"""
Task case 217: interface_sink_bridge_02 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_217_interface_sink_bridge_02(input_data):
    task_name = 'interface_sink_bridge_02'
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
