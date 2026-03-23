"""
Task case 254: thread_pool_capture_05 deep stress pattern.
"""

RETAINED_CACHE = {}
RETAINED_AUDIT = []
RETAINED_HANDLERS = []

def case_254_thread_pool_capture_05(input_data):
    task_name = 'thread_pool_capture_05'
    raw = input_data or 'sample'
    payload = {
        'task': task_name,
        'entity': 'extreme',
        'stage': 'stress',
        'input': raw,
        'checksum': f'{task_name}:{len(raw)}',
    }
    import threading
    # ESCAPE: thread captures payload and retains after return edge.
    threading.Thread(target=lambda: RETAINED_AUDIT.append(payload), daemon=True).start()
    return 'ok'
