"""
Task case 125: thread_handoff_late_03 false-positive/false-negative stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_125_thread_handoff_late_03(input_data):
    task_name = 'thread_handoff_late_03'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'stress',
        'stage': 'evaluation',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    import threading
    # ESCAPE: payload is captured by background thread closure.
    threading.Thread(target=lambda: RETAINED_AUDIT.append(payload), daemon=True).start()
    return 'ok'
