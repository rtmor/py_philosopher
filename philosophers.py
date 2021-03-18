import threading
import random
import time
import math


# class Fork(object):

#     def __init__(self):
#         self.__lock = threading.Lock()

#     def acquire(self, block):
#         return self.__lock.acquire(blocking=block)

#     def release(self):
#         self.__lock.release()


class Hunger(threading.Thread):
    def __init__(self, philosopher_id: int):
        self.uid = philosopher_id
        self.hunger = 100
        threading.Thread.__init__(self)

    def run(self):
        if self.starved():
            return

        print(f"phil {self.uid} hunger: {self.hunger}")
        threading.Timer(3, self.run).start()
        self.hunger -= 10

    def fill(self, amount: int):
        level = self.hunger + amount
        self.hunger = 100 if level > 100 else level

    def starved(self):
        return self.hunger <= 0


class Philosopher(threading.Thread):
    def __init__(self, uid: int, forkLeft: threading.Lock, forkRight: threading.Lock):
        self.uid = uid
        self.forkLeft = forkLeft
        self.forkRight = forkRight
        self.hunger = Hunger(philosopher_id=uid)

        threading.Thread.__init__(self)

    def run(self):
        self.hunger.start()

        while not self.hunger.starved():
            self.ponder()
            self.eat()

        print(f"Philosopher {self.uid} ded")

    def ponder(self):
        print(f"Philosopher {self.uid} is in thought...")
        time_in_thought = random.randint(1, 10)
        time.sleep(float(time_in_thought))

    def eat(self):
        time_eating = float(random.randint(1, 10))
        self.forkLeft.acquire(blocking=True)

        acquired = self.forkRight.acquire(blocking=False)
        if not acquired:
            self.forkLeft.release()
            return

        # start eating!
        print(f"Philosopher {self.uid} begins eating")
        self.hunger.fill(20)
        time.sleep(time_eating)
        print(f"Philosopher {self.uid} finishes eating")

        self.forkLeft.release()
        self.forkRight.release()


PHILOSOPHER_COUNT = 5


def main():
    # init five (5) 'forks' for the five philosophers
    forks = [threading.Lock() for f in range(PHILOSOPHER_COUNT)]

    # init five (5) philosophers
    philosophers = [
        Philosopher(
            uid=i,
            forkLeft=forks[i % PHILOSOPHER_COUNT],
            forkRight=forks[(i + 1) % PHILOSOPHER_COUNT])
        for i in range(PHILOSOPHER_COUNT)
    ]

    for philosopher in philosophers:
        philosopher.start()


if __name__ == '__main__':
    main()
