import threading
import time


def no_threads(_input_data):
    return "ok"


def join_thread(_input_data):
    def worker():
        time.sleep(0.1)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    return "ok"


def join_daemon_thread(_input_data):
    def worker():
        time.sleep(0.1)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join()
    return "ok"


def join_multiple_threads(_input_data):
    def worker():
        time.sleep(0.1)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return "ok"


def cancel_timer_thread(_input_data):
    timer = threading.Timer(0.5, lambda: None)
    timer.start()
    timer.cancel()
    timer.join()
    return "ok"
