from heapq import heappush, heappop
from random import shuffle
from typing import List, Tuple

from core.music.sources import MartAudio


class Queue:
    """ FIFO Queue """
    def __init__(self):
        self.queue: List[MartAudio] = []

    def __bool__(self) -> bool:
        return self.queue != []

    def add(self, source: MartAudio, **kwargs):
        self.queue.append(source)

    def get(self) -> MartAudio:
        return self.queue.pop(0)

    def clear(self):
        self.queue.clear()

    def cleanup(self):
        for song in self.queue:
            song.cleanup()

    def shuffle(self):
        shuffle(self.queue)


class ChunkedQueue(Queue):
    """ FIFO in chunks """

    def __init__(self,
                 chunk_size=2,
                 max_chunks=-1,
                 max_per_user=-1):
        self.size = chunk_size
        self.max = max_chunks
        self.user_max = max_per_user
        self.items: List[List[Tuple[int, MartAudio]]] = []
        super().__init__()
        self.queue: List[Tuple[int, MartAudio]]

    def __bool__(self) -> bool:
        return self._queue != []

    def _error(self, err):
        raise Exception(err)

    @property
    def _queue(self):
        r = self.queue[:]
        for group in self.items:
            r += group
        return r

    async def add(self, source: MartAudio, requester_id: int = None, **kwargs):
        # === LOGIC ===
        # Basically, the first thing is to find the index of the user's
        # last song (since when they add something new, it should always be
        # added after their other songs)
        # This is achieved by iterating backwards through the queue queue,
        # stopping the first time something by that user is found
        # Next, we iterate forward from that starting point.
        # For each song, we put the user that added it into a set.
        # We continue to move forward this way until we hit a user that
        # is already in the set. We stop here and insert the source.

        # For users A, B, and C, imagine starting queue ABCABCABCBBBBB

        # User A tries to put something in the queue
        #       v last A, start here
        # ABCABCABCBBBBB
        # B goes into the set
        # C goes into the set
        # B is already in the set, so the A gets added here
        # ABCABCABCABBBBB

        entry = (requester_id, source)

        if not self.items:
            self.items.append([entry])
            return

        if len(self.items) == self.max:
            self._error("Max queue chunks reached.")

        x = 0
        for chunk in self.items:
            if chunk[0][0] == requester_id and len(chunk) == self.size:
                x += 1

        if x == self.user_max:
            self._error("User reached maximum amount of chunks")

        # Insert the data
        # print("Iterating backwards")
        for index, value in enumerate(reversed(self.items)):
            # print(index)
            if index == len(self.items) - 1 or value[0][0] == requester_id:
                # we found the last source by us or
                # we have no items in the queue

                if value[0][0] == requester_id and len(value) < self.size:
                    # last source by us has a free space left
                    value.append(entry)
                    return

                # index to start from
                # python is 0-indexed so subtract 1
                start = len(self.items) - index - 1
                found_ids = []

                # Easier than `enumerate` in this case
                # print("Iterating forward")
                while True:
                    # print(start)
                    if start >= len(self.items):
                        # print("Inserting at the end")
                        # No place left, put it at the end
                        self.items.append([entry])
                        return

                    requester_id = self.items[start][0][0]

                    if requester_id in found_ids:
                        # print("Duplicate found, inserting")
                        # this id appears for the second time now
                        # so insert here
                        self.items.insert(start, [entry])
                        return

                    # Add the id to the list
                    found_ids.append(requester_id)

                    start += 1

    def shuffle(self):
        old = self.queue[:]
        self.clear()
        shuffle(old)
        for (requester, source) in old:
            self.add(source, requester_id=requester)

    def get(self) -> MartAudio:
        if not self._queue:
            # Load the next chunk
            # we use `pop` to make sure it disappears from the original list
            # because otherwise people could queue up forever
            self.queue = self.items.pop(0)
        return self._queue.pop(0)[1]

    def clear(self):
        for i in self._queue:
            i.cleanup()
        self.items.clear()
        self.queue.clear()

    def cleanup(self):
        for i in self._queue:
            i.cleanup()


class PriorityQueue(Queue):
    def __init__(self):
        super().__init__()
        self._index = 0

    def add(self, source: MartAudio, priority: int = 0, **kwargs):
        heappush(self.queue, (-priority, self._index, source))
        self._index += 1

    def get(self) -> MartAudio:
        return heappop(self.queue)

    def shuffle(self):
        old = self.queue[:]
        self.queue = []
        shuffle(old)
        for priority, _, source in old:
            self.add(source, -priority)


class ChunkedPriorityQueue(Queue):
    pass


class QUEUE:
    Simple = Queue
    Chunked = ChunkedQueue
    Priority = PriorityQueue
    ChunkedPriority = ChunkedPriorityQueue
