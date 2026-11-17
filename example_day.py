"""A day in the life of a Minervan in Tokyo.

Run:  python example_day.py
"""

from scheduler import Task, TaskScheduler

H = 60  # minutes per hour

TOKYO_DAY = [
    Task(1, "Morning exercise", 30, [], importance=6, enjoyment=7, deadline_min=9 * H),
    Task(2, "Buying produce at 7/11", 25, [1], importance=7, enjoyment=5),
    Task(3, "Cook food", 60, [2], importance=7, enjoyment=6),
    Task(4, "Study for class", 80, [], importance=9, enjoyment=4, deadline_min=18 * H),
    Task(5, "CS110 at 6PM", 90, [4], importance=10, enjoyment=5, earliest_start_min=18 * H),
    Task(6, "Travel on train", 40, [3, 5], importance=7, enjoyment=6),
    Task(7, "Visit Senso-ji Temple", 40, [5, 6], importance=6, enjoyment=8),
    Task(8, "Go to Japanese karaoke", 120, [5, 6], importance=4, enjoyment=9),
    Task(9, "Eat ramen", 40, [6], importance=7, enjoyment=9),
]


if __name__ == "__main__":
    scheduler = TaskScheduler(TOKYO_DAY)
    scheduler.print_self()
    print()
    scheduler.run_task_scheduler(starting_time=9 * H)
