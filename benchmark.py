"""Measure how the scheduler's runtime grows with the number of tasks.

Run:  python benchmark.py   (saves docs/scaling.png)

Random-task generator repurposed from the CS110 Session 16 PCW
("Randomly built BSTs"), where I plotted BST scaling.
"""

import math
import random
import statistics
import time
from pathlib import Path

import matplotlib.pyplot as plt

from scheduler import MaxHeapq, Task, TaskScheduler

SIZES = [100, 250, 500, 1000, 2000, 4000]
REPEATS = 3


def generate_random_tasks(n, rng):
    """n tasks with random attributes; ~10% have a dependency, ~5% a fixed start."""
    tasks = []
    for i in range(1, n + 1):
        dependencies = [rng.randint(1, i - 1)] if i > 1 and rng.random() < 0.1 else []
        earliest_start = rng.randint(300, 1080) if rng.random() < 0.05 else None
        tasks.append(Task(
            id=i,
            description=f"Task {i}",
            duration=rng.randint(10, 120),
            dependencies=dependencies,
            importance=rng.randint(3, 10),
            enjoyment=rng.randint(3, 10),
            earliest_start_min=earliest_start,
        ))
    return tasks


def time_scheduler(n, rng):
    tasks = generate_random_tasks(n, rng)
    scheduler = TaskScheduler(tasks, verbose=False)
    start = time.perf_counter()
    scheduler.run_task_scheduler(starting_time=8 * 60)
    return time.perf_counter() - start


def time_heap_only(n, rng):
    """n pushes followed by n pops: the heap on its own."""
    keys = [rng.random() for _ in range(n)]
    heap = MaxHeapq()
    start = time.perf_counter()
    for k in keys:
        heap.heappush(k)
    for _ in range(n):
        heap.heappop()
    return time.perf_counter() - start


def median_time(fn, n, seed):
    return statistics.median(fn(n, random.Random(seed + r)) for r in range(REPEATS))


def fit(reference, measured):
    """Scale a reference curve to match the largest measurement."""
    scale = measured[-1] / reference[-1]
    return [scale * x for x in reference]


if __name__ == "__main__":
    sched = [median_time(time_scheduler, n, 0) for n in SIZES]
    heap = [median_time(time_heap_only, n, 100) for n in SIZES]

    for n, s, h in zip(SIZES, sched, heap):
        print(f"n={n:5d}  scheduler={s * 1000:9.1f} ms   heap only={h * 1000:7.2f} ms")

    nlogn = [n * math.log2(n) for n in SIZES]
    n2 = [n * n for n in SIZES]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    ax = axes[0]
    ax.plot(SIZES, heap, "o-", label="Measured")
    ax.plot(SIZES, fit(nlogn, heap), "--", label="O(n log n) reference")
    ax.set_title("MaxHeapq: n pushes + n pops")

    ax = axes[1]
    ax.plot(SIZES, sched, "o-", label="Measured")
    ax.plot(SIZES, fit(nlogn, sched), "--", label="O(n log n) reference")
    ax.plot(SIZES, fit(n2, sched), ":", label="O(n²) reference")
    ax.set_title("Full scheduler run")

    for ax in axes:
        ax.set_xlabel("Number of tasks (n)")
        ax.set_ylabel("Runtime (s)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()

    fig.tight_layout()
    out = Path(__file__).parent / "docs" / "scaling.png"
    fig.savefig(out, dpi=150)
    print(f"Saved {out}")
