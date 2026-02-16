import multiprocessing as mp
import time

REQUIRES_MAIN_THREAD = True


def _pool_worker():
    time.sleep(0.1)


def close_process_pool(_input_data):
    pool = mp.Pool(processes=1)
    pool.apply_async(_pool_worker)
    pool.close()
    pool.join()
    return "ok"


def close_process_pool_multiple(_input_data):
    pool = mp.Pool(processes=2)
    pool.apply_async(_pool_worker)
    pool.apply_async(_pool_worker)
    pool.close()
    pool.join()
    return "ok"


def close_process_pool_context(_input_data):
    with mp.Pool(processes=1) as pool:
        pool.apply_async(_pool_worker)
    return "ok"
