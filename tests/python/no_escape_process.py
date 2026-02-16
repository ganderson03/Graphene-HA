import multiprocessing as mp
import time

REQUIRES_MAIN_THREAD = True


def _worker():
    time.sleep(0.1)


def join_process(_input_data):
    process = mp.Process(target=_worker)
    process.start()
    process.join()
    return "ok"


def join_multiple_processes(_input_data):
    processes = [mp.Process(target=_worker) for _ in range(2)]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    return "ok"
