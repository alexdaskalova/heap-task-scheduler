"""Utility-driven daily task scheduler.

The scheduler repeatedly picks the ready task with the highest utility,
using a max-heap as the priority queue. A task is ready when all of its
dependencies are done and its earliest start time (if any) has arrived.

Skeleton adapted from the CS110 Session 13 PCW ("Heaps and priority queues").
"""

import math

from .max_heap import MaxHeapq

# Utility weights: urgency, importance, duration score, enjoyment
WEIGHTS = {"urgency": 0.4, "importance": 0.3, "duration": 0.2, "enjoyment": 0.1}


def format_time(minutes):
    """Format minutes as ``HhMM`` (e.g. 545 -> '9h05')."""
    return f"{minutes // 60}h{minutes % 60:02d}"


class Task:
    """
    A single activity in the day.

    Attributes
    ----------
    id : int
        Unique task ID that other tasks can reference.
    description : str
        Short description of the task.
    duration : int
        Duration in minutes.
    dependencies : list[int]
        IDs of tasks that must finish before this one starts.
    importance : int
        How critical the task is for health and goals (1-10).
    enjoyment : int
        How pleasant or fun the task is (1-10).
    deadline_min : int or None
        Time (minutes after midnight) by which the task should be done.
    earliest_start_min : int or None
        Time (minutes after midnight) before which the task cannot start.
        Used for fixed events such as "class starts at 6 PM".
    status : str
        'N' = not started, 'I' = in the queue, 'C' = completed.
    """

    def __init__(self, id, description, duration, dependencies,
                 importance, enjoyment, deadline_min=None,
                 earliest_start_min=None, status="N"):
        self.id = id
        self.description = description
        self.duration = duration
        self.dependencies = list(dependencies)
        self.importance = importance
        self.enjoyment = enjoyment
        self.deadline_min = deadline_min
        self.earliest_start_min = earliest_start_min
        self.status = status

    def copy(self):
        """Return an independent copy (dependency list included)."""
        return Task(self.id, self.description, self.duration, self.dependencies,
                    self.importance, self.enjoyment, self.deadline_min,
                    self.earliest_start_min, self.status)

    # --- Components of the utility function -------------------------------

    def compute_deadline_urgency(self, current_min):
        """
        Urgency score (3-10) based on how much slack is left.

        - No deadline: baseline urgency 3, or 10 once a fixed start time
          has arrived.
        - With a deadline: slack = deadline - now - duration. Less slack
          means more urgency, up to 10 when there is no slack left.
        """
        if self.deadline_min is None:
            if self.earliest_start_min is not None and current_min >= self.earliest_start_min:
                return 10
            return 3

        slack = self.deadline_min - current_min - self.duration
        if slack <= 0:
            return 10
        if slack <= self.duration:
            return 9
        if slack <= 2 * self.duration:
            return 7
        if slack <= 4 * self.duration:
            return 5
        return 3

    def compute_duration_score(self):
        """
        Duration score (3-9): shorter tasks score higher, since they are
        easier to fit in and more rewarding to check off.
        """
        d = self.duration
        if d >= 120:
            return 3
        if d >= 90:
            return 4
        if d >= 60:
            return 5
        if d >= 45:
            return 6
        if d >= 30:
            return 7
        if d >= 15:
            return 8
        return 9

    def compute_utility(self, current_min):
        """
        Utility = 0.4*U + 0.3*I + 0.2*D + 0.1*E

        U = urgency (depends on the current time), I = importance,
        D = duration score, E = enjoyment.
        """
        return (WEIGHTS["urgency"] * self.compute_deadline_urgency(current_min)
                + WEIGHTS["importance"] * self.importance
                + WEIGHTS["duration"] * self.compute_duration_score()
                + WEIGHTS["enjoyment"] * self.enjoyment)

    def __repr__(self):
        return f"Task({self.id}, '{self.description}')"


class TaskScheduler:
    """Daily task scheduler driven by a max-priority queue."""

    NOT_STARTED = "N"
    IN_PRIORITY_QUEUE = "I"
    COMPLETED = "C"

    def __init__(self, tasks, heap_class=MaxHeapq, verbose=True):
        """
        Parameters
        ----------
        tasks : list[Task]
            Tasks to schedule. They are copied, so the caller's list is
            never modified and can be reused for another run.
        heap_class : type
            Priority queue class (defaults to MaxHeapq).
        verbose : bool
            Print progress while running.
        """
        self.tasks = [t.copy() for t in tasks]
        self.priority_queue = heap_class()
        self.verbose = verbose
        self.schedule = []  # (start_min, end_min, task) in execution order

    def _log(self, message):
        if self.verbose:
            print(message)

    def print_self(self):
        """Print every task and its dependencies."""
        print("Tasks added to the scheduler:")
        print("--------------------------------------")
        for t in self.tasks:
            print(f"➡️ '{t.description}', duration = {t.duration} mins.")
            if t.dependencies:
                print(f"\t⚠️ Depends on tasks: {t.dependencies}")

    def _build_dependency_graph(self):
        """
        Index the tasks once so the main loop never has to rescan them:
        - ``dependents[id]``: tasks waiting on task ``id``
        - ``remaining[id]``: how many of task ``id``'s dependencies are unfinished
        - ``unlocked``: tasks whose dependencies are all done (ready, or
          waiting for their earliest start time)

        Dependencies on IDs that don't exist can never be met, so such
        tasks are never unlocked.
        """
        ids = {t.id for t in self.tasks}
        self.dependents = {t.id: [] for t in self.tasks}
        self.remaining = {}
        self.unlocked = []
        for t in self.tasks:
            deps = set(t.dependencies)
            self.remaining[t.id] = len(deps) if deps <= ids else math.inf
            for d in deps & ids:
                self.dependents[d].append(t)
            if self.remaining[t.id] == 0:
                self.unlocked.append(t)

    def _complete(self, task):
        """Mark ``task`` done and unlock the tasks that were waiting on it."""
        task.status = self.COMPLETED
        for t in self.dependents[task.id]:
            self.remaining[t.id] -= 1
            if self.remaining[t.id] == 0:
                self.unlocked.append(t)

    def get_tasks_ready(self, current_min):
        """
        Move unlocked tasks into the right queue:
        - can start now -> priority queue, keyed by utility at ``current_min``
        - fixed start in the future -> waiting queue, ordered by start time

        Then release any waiting tasks whose start time has arrived.
        The order of the input list does not affect the result.
        """
        for task in self.unlocked:
            if task.earliest_start_min is not None and current_min < task.earliest_start_min:
                # MaxHeapq with negated keys acts as a min-heap on start time
                self.waiting.heappush((-task.earliest_start_min, -task.id, task))
            else:
                self._enqueue(task, current_min)
        self.unlocked = []

        while len(self.waiting) > 0 and -self.waiting.peek()[0] <= current_min:
            _, _, task = self.waiting.heappop()
            self._enqueue(task, current_min)

    def _enqueue(self, task, current_min):
        task.status = self.IN_PRIORITY_QUEUE
        priority = task.compute_utility(current_min)
        self.priority_queue.heappush((priority, task.id, task))

    def next_earliest_start(self):
        """Start time of the next waiting task, or None if none is waiting."""
        if len(self.waiting) == 0:
            return None
        return -self.waiting.peek()[0]

    def run_task_scheduler(self, starting_time):
        """
        Run tasks in priority order until all are done.

        Parameters
        ----------
        starting_time : int
            Start of the day, in minutes after midnight.

        Returns
        -------
        list[tuple[int, int, Task]]
            The schedule as (start_min, end_min, task) tuples.
        """
        current_min = starting_time
        self.schedule = []
        self.waiting = MaxHeapq()  # unlocked tasks whose fixed start is still ahead
        self._build_dependency_graph()
        self._log("Running the scheduler:\n")

        while len(self.schedule) < len(self.tasks):
            self.get_tasks_ready(current_min)

            if len(self.priority_queue) > 0:
                _, _, task = self.priority_queue.heappop()
                start = current_min
                current_min += task.duration
                self._log(f"🕰 t={format_time(start)}")
                self._log(f"\tStarted '{task.description}' (ID={task.id}) for {task.duration} mins...")
                self._log(f"\t✅ t={format_time(current_min)}, task completed!")

                self._complete(task)
                self.schedule.append((start, current_min, task))
                continue

            # Nothing is ready: jump ahead to the next fixed start time.
            next_time = self.next_earliest_start()
            if next_time is None:
                self._log("⚠️ Attention: some tasks can never be scheduled "
                          "(circular or missing dependencies).")
                break
            self._log(f"⏭ No tasks ready; jumping from {format_time(current_min)} "
                      f"to {format_time(next_time)} to wait for tasks.")
            current_min = next_time

        self._log(f"\n🏁 Completed all planned tasks in {format_time(current_min - starting_time)}!")
        return self.schedule
