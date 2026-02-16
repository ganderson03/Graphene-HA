import threading
import time

_leaked_threads = []


def spawn_global_thread(_input_data):
    def worker():
        time.sleep(2)

    thread = threading.Thread(target=worker)
    thread.start()
    _leaked_threads.append(thread)
    return "ok"


def spawn_named_global_thread(_input_data):
    def worker():
        time.sleep(2)

    thread = threading.Thread(target=worker, name="global-worker")
    thread.start()
    _leaked_threads.append(thread)
    return "ok"


def spawn_multiple_global_threads(_input_data):
    def worker():
        time.sleep(2)

    for idx in range(3):
        thread = threading.Thread(target=worker, name=f"global-worker-{idx}")
        thread.start()
        _leaked_threads.append(thread)
    return "ok"


def spawn_global_timer_thread(_input_data):
    timer = threading.Timer(2.0, lambda: None)
    timer.start()
    _leaked_threads.append(timer)
    return "ok"


def spawn_global_waiting_thread(_input_data):
    event = threading.Event()

    def worker():
        event.wait()

    thread = threading.Thread(target=worker, name="global-waiter")
    thread.start()
    _leaked_threads.append(thread)
    return "ok"
