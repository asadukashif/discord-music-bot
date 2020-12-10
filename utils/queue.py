
from typing import Any, List
from itertools import permutations
import random
from .song import Song


class Queue():
    def __init__(self) -> None:
        self.queue = []

    def push(self, node: Song) -> None:
        self.queue.append(node)

    def pop(self) -> dict:
        if self.get_size() > 0:
            return self.queue.pop(0)
        else:
            return None

    def clear(self) -> None:
        self.queue = []

    def as_list(self) -> List[dict]:
        return self.queue

    def get_size(self) -> int:
        return len(self.queue)

    def shuffle(self) -> None:
        shuffled_queue = list(permutations(self.queue))
        random_index = random.randint(0, len(shuffled_queue))
        self.queue = list(shuffled_queue[random_index])

    def skip_to(self, index: int) -> bool:
        if index <= self.get_size():
            self.queue = self.queue[index-1:]
            return True
        return False

    def push_to_start(self, node: Song) -> None:
        self.queue.insert(0, node)

    def replace(self, src_index: int, dest_index: int) -> bool:
        if src_index > self.get_size() or dest_index > self.get_size():
            return False

        tmp = self.queue[src_index - 1]
        self.queue[src_index - 1] = self.queue[dest_index - 1]
        self.queue[dest_index - 1] = tmp

        return True

    def delete(self, index: int) -> bool:
        if index <= self.get_size():
            self.queue.pop(index-1)
            return True
        return False
