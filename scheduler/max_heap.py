"""A max-priority queue built on a binary heap stored in a Python list.

Adapted from the CS110 Session 13 PCW ("Heaps and priority queues"),
with edits made in class and afterwards.
"""


class MaxHeapq:
    """
    Max-priority queue backed by a binary heap.

    Keys can be anything comparable (ints, floats, tuples). The scheduler
    pushes ``(priority, task_id, task)`` tuples, so ties on priority are
    broken by task ID.

    Attributes
    ----------
    heap : list
        Keys stored in heap order; the largest key is always at index 0.
    heap_size : int
        Number of keys currently in the heap.
    """

    def __init__(self):
        self.heap = []
        self.heap_size = 0

    def __len__(self):
        return self.heap_size

    @staticmethod
    def left(i):
        """Index of the left child of node ``i``."""
        return 2 * i + 1

    @staticmethod
    def right(i):
        """Index of the right child of node ``i``."""
        return 2 * i + 2

    @staticmethod
    def parent(i):
        """Index of the parent of node ``i``."""
        return (i - 1) // 2

    def peek(self):
        """Return the largest key without removing it."""
        if self.heap_size < 1:
            raise IndexError("peek from an empty priority queue")
        return self.heap[0]

    def heappush(self, key):
        """
        Insert ``key`` and bubble it up until the max-heap property holds.

        Complexity: O(log n).
        """
        self.heap.append(key)
        self.heap_size += 1
        i = self.heap_size - 1

        # Swap with the parent while the parent is smaller (bubble up).
        # This removes the need for a separate increase_key method.
        while i > 0 and self.heap[self.parent(i)] < self.heap[i]:
            j = self.parent(i)
            self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
            i = j

    def heapify(self, i):
        """
        Restore the max-heap property for the subtree rooted at ``i``
        by sifting the node down.

        Complexity: O(log n).
        """
        heap = self.heap
        while True:
            l, r = self.left(i), self.right(i)
            largest = i
            if l < self.heap_size and heap[l] > heap[largest]:
                largest = l
            if r < self.heap_size and heap[r] > heap[largest]:
                largest = r
            if largest == i:
                return
            heap[i], heap[largest] = heap[largest], heap[i]
            i = largest

    def heappop(self):
        """
        Remove and return the largest key.

        Complexity: O(log n).
        """
        if self.heap_size < 1:
            raise IndexError("pop from an empty priority queue")
        max_key = self.heap[0]
        # Move the last element to the root, then sift it down.
        self.heap[0] = self.heap[-1]
        self.heap.pop()
        self.heap_size -= 1
        self.heapify(0)
        return max_key
