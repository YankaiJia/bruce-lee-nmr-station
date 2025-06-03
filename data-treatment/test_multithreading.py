"""
This script should make your computer run at maximum CPU usage.
If not, something is wrong.
"""

import os
import multiprocessing
NUM_CPU_CORES = multiprocessing.cpu_count()  # get the number of CPU cores

from concurrent.futures import ProcessPoolExecutor
import time

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

def heavy_compute(i):
    total = 0
    for _ in range(10000000):
        total += sum(j * j for j in range(100))
    return total

if __name__ == "__main__":
    print(f"Number of CPU cores: {NUM_CPU_CORES}")
    start = time.time()
    with ProcessPoolExecutor(max_workers=NUM_CPU_CORES) as executor:
        results = list(executor.map(heavy_compute, range(32)))
    print(f"Elapsed: {time.time() - start:.2f}s")
