import time
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=1)
_leaked_executors = []


def leak_executor(_input_data):
    _executor.submit(time.sleep, 2)
    return "ok"


def leak_executor_submit_many(_input_data):
    _executor.submit(time.sleep, 2)
    _executor.submit(time.sleep, 2)
    return "ok"


def leak_new_executor(_input_data):
    executor = ThreadPoolExecutor(max_workers=1)
    _leaked_executors.append(executor)
    executor.submit(time.sleep, 2)
    return "ok"


def leak_new_executor_multiple(_input_data):
    executor = ThreadPoolExecutor(max_workers=2)
    _leaked_executors.append(executor)
    executor.submit(time.sleep, 2)
    executor.submit(time.sleep, 2)
    return "ok"


def shutdown_executor(_input_data):
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(time.sleep, 0.1)
    return "ok"
