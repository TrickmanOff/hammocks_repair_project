import time


def timeit(func):
    def wrapper_func(*args, **kwargs):
        st_time = time.time()
        func_res = func(*args, **kwargs)
        end_time = time.time()
        return end_time - st_time, func_res
    return wrapper_func
