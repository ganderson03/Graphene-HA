import multiprocessing as mp
import time

REQUIRES_MAIN_THREAD = True

_POOL = None
_POOL2 = None


def _pool_worker():
    time.sleep(2)


def _pool_worker_with_arg(_value):
    time.sleep(2)


def leak_process_pool(_input_data):
    global _POOL
    if _POOL is None:
        _POOL = mp.Pool(processes=1)
    _POOL.apply_async(_pool_worker)
    return "ok"


def leak_process_pool_multiple(_input_data):
    global _POOL
    if _POOL is None:
        _POOL = mp.Pool(processes=2)
    _POOL.apply_async(_pool_worker)
    _POOL.apply_async(_pool_worker)
    return "ok"


def leak_process_pool_map_async(_input_data):
    global _POOL2
    if _POOL2 is None:
        _POOL2 = mp.Pool(processes=1)
    _POOL2.map_async(_pool_worker_with_arg, [0])
    return "ok"
