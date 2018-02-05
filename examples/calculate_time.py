import time


def calculate_time(f, *args, loops=1):
    result = 0
    for i in range(0, loops):
        start_time = time.time()
        f(*args)
        result += time.time() - start_time
    return result / loops
