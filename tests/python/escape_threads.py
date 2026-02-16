import threading
import time


def spawn_non_daemon_thread(_input_data):
    def worker():
        time.sleep(2)

    thread = threading.Thread(target=worker)
    thread.start()
    return "ok"


def spawn_daemon_thread(_input_data):
    def worker():
        time.sleep(2)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return "ok"


def spawn_timer_thread(_input_data):
    timer = threading.Timer(2.0, lambda: None)
    timer.start()
    return "ok"


def spawn_named_thread(_input_data):
    def worker():
        time.sleep(2)

    thread = threading.Thread(target=worker, name="named-worker")
    thread.start()
    return "ok"


def spawn_multiple_threads(_input_data):
    def worker():
        time.sleep(2)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    return "ok"


def spawn_nested_thread(_input_data):
    def inner_worker():
        time.sleep(2)

    def worker():
        inner = threading.Thread(target=inner_worker)
        inner.start()
        time.sleep(2)

    thread = threading.Thread(target=worker)
    thread.start()
    return "ok"


def spawn_waiting_thread(_input_data):
    event = threading.Event()

    def worker():
        event.wait()

    thread = threading.Thread(target=worker)
    thread.start()
    return "ok"
