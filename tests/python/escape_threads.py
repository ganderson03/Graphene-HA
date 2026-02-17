import test_helpers as h


def spawn_non_daemon_thread(_input_data):
    return h.spawn_worker(daemon=False)


def spawn_daemon_thread(_input_data):
    return h.spawn_worker(daemon=True)


def spawn_timer_thread(_input_data):
    return h.spawn_timer(interval=2.0)


def spawn_named_thread(_input_data):
    return h.spawn_named_worker(name="named-worker")


def spawn_multiple_threads(_input_data):
    return h.spawn_multiple_workers(count=3)


def spawn_nested_thread(_input_data):
    return h.spawn_nested_workers()


def spawn_waiting_thread(_input_data):
    return h.spawn_event_waiter()
