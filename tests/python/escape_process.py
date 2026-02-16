import multiprocessing as mp
import time

REQUIRES_MAIN_THREAD = True


def _worker():
    time.sleep(2)


def spawn_process(_input_data):
    process = mp.Process(target=_worker)
    process.start()
    return "ok"


def spawn_multiple_processes(_input_data):
    processes = [mp.Process(target=_worker) for _ in range(2)]
    for process in processes:
        process.start()
    return "ok"


def spawn_daemon_process(_input_data):
    process = mp.Process(target=_worker)
    process.daemon = True
    process.start()
    return "ok"
