import test_helpers as h


def no_threads(_input_data):
    return "ok"


def join_thread(_input_data):
    return h.join_worker(delay=0.1)


def join_daemon_thread(_input_data):
    return h.join_daemon_worker(delay=0.1)


def join_multiple_threads(_input_data):
    return h.join_multiple_workers(count=3, delay=0.1)


def cancel_timer_thread(_input_data):
    return h.cancel_timer(interval=0.5)
