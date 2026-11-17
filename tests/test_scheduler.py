import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from example_day import TOKYO_DAY  # noqa: E402
from scheduler import MaxHeapq, Task, TaskScheduler  # noqa: E402


# --- MaxHeapq ---------------------------------------------------------------

def drain(heap):
    return [heap.heappop() for _ in range(len(heap))]


@pytest.mark.parametrize("values", [
    [3, 1, 5, 2, 4],
    [0, -1, 0, 7, 7, 5, 5],   # duplicates and negatives
    [42],
])
def test_heap_pops_in_descending_order(values):
    heap = MaxHeapq()
    for v in values:
        heap.heappush(v)
    assert drain(heap) == sorted(values, reverse=True)


def test_heap_matches_sorted_on_random_input():
    rng = random.Random(0)
    values = [rng.uniform(-100, 100) for _ in range(1000)]
    heap = MaxHeapq()
    for v in values:
        heap.heappush(v)
    assert drain(heap) == sorted(values, reverse=True)


def test_heap_empty_pop_raises():
    with pytest.raises(IndexError):
        MaxHeapq().heappop()


# --- TaskScheduler ----------------------------------------------------------

def order(tasks, start=9 * 60):
    schedule = TaskScheduler(tasks, verbose=False).run_task_scheduler(start)
    return [task.id for _, _, task in schedule]


def test_tokyo_day_schedule():
    schedule = TaskScheduler(TOKYO_DAY, verbose=False).run_task_scheduler(9 * 60)
    assert [t.id for _, _, t in schedule] == [1, 2, 4, 3, 5, 6, 9, 7, 8]
    # CS110 starts exactly at 6 PM, after the idle gap
    class_start = next(start for start, _, t in schedule if t.id == 5)
    assert class_start == 18 * 60


def test_input_order_does_not_change_schedule():
    assert order(TOKYO_DAY) == order(list(reversed(TOKYO_DAY)))


def test_dependencies_are_respected():
    schedule = TaskScheduler(TOKYO_DAY, verbose=False).run_task_scheduler(9 * 60)
    finished_at = {t.id: end for _, end, t in schedule}
    for start, _, task in schedule:
        original = next(t for t in TOKYO_DAY if t.id == task.id)
        for dep in original.dependencies:
            assert finished_at[dep] <= start


def test_scheduler_does_not_mutate_input():
    before = [list(t.dependencies) for t in TOKYO_DAY]
    order(TOKYO_DAY)
    assert [list(t.dependencies) for t in TOKYO_DAY] == before


def test_circular_dependencies_stop_cleanly():
    tasks = [
        Task(1, "A", 10, [2], importance=5, enjoyment=5),
        Task(2, "B", 10, [1], importance=5, enjoyment=5),
        Task(3, "C", 10, [], importance=5, enjoyment=5),
    ]
    assert order(tasks) == [3]


def test_urgency_rises_as_deadline_nears():
    task = Task(1, "Essay", 60, [], importance=5, enjoyment=5, deadline_min=600)
    urgencies = [task.compute_deadline_urgency(now) for now in (0, 300, 450, 500, 540)]
    assert urgencies == sorted(urgencies)
    assert urgencies[-1] == 10
