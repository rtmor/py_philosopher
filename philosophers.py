import threading
import enlighten
import random
import time
import math
import sys


# Fork is a threading.Lock() wrapper
class Fork(object):
    def __init__(self):
        self.__lock = threading.Lock()

    def acquire(self, blocking=True, timeout=None):
        return self.__lock.acquire(blocking)

    def release(self):
        self.__lock.release()


class Hunger(threading.Thread):
    def __init__(self, philosopher_id: int):
        self.uuid = philosopher_id
        self.active = True
        self.hunger = 100
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        while self.active:
            rate_of_starvation = float(random.randint(2, 5))
            qnt_of_starvation = float(random.randint(5, 15))

            self.deplete(qnt_of_starvation)
            time.sleep(rate_of_starvation)

    def fill(self, amount: int):
        hunger_level = self.hunger + amount
        self.hunger = 100.0 if hunger_level > 100.0 else hunger_level

    def deplete(self, amount: int):
        hunger_level = self.hunger - amount
        self.hunger = 0.0 if hunger_level <= 0.0 else hunger_level

    def get_hunger(self):
        return self.hunger

    def starved(self):
        return self.hunger <= 0.0


class Philosopher(threading.Thread):
    def __init__(self, uuid: int, forkLeft: Fork, forkRight: Fork):
        self.uuid = uuid
        self.hunger = Hunger(philosopher_id=uuid)
        self.feasting = False
        self.forkLeft = forkLeft
        self.forkRight = forkRight

        threading.Thread.__init__(self)

    def run(self):
        self.hunger.start()

        while not self.hunger.starved():
            self.ponder()
            self.try_eat()

        self.__clean_up()

    def ponder(self):
        time_in_thought = random.randint(1, 4)
        time.sleep(float(time_in_thought))

    def try_eat(self):
        self.forkLeft.acquire(blocking=True)  # be greedy

        acquired = self.forkRight.acquire(blocking=False)
        if not acquired:
            self.forkLeft.release()
            return

        # start eating!
        self.feast()
        self.forkLeft.release()
        self.forkRight.release()

    def feast(self):
        self.feasting = True

        time_eating = float(random.randint(1, 5))
        self.hunger.fill(20 * (time_eating / 5))
        time.sleep(time_eating)

        self.feasting = False

    def is_feasting(self):
        return self.feasting

    def __clean_up(self):
        self.hunger.active = False


class Monitor():
    def __init__(self, philosophers: list()):
        self.manager = enlighten.get_manager()
        self.status_bars = list()
        self.philosophers = philosophers
        self.dead_count = 0

    def start(self):
        with self.manager:
            for philosopher in self.philosophers:
                status_format = '{philosopher}{fill}Status: {status}{fill} Hunger: {hunger}'
                status_bar = self.manager.status_bar(status_format=status_format,
                                                     color='green',
                                                     philosopher=f'Philosopher {philosopher.uuid}',
                                                     status=f'{"thinking":10}',
                                                     hunger=f'{philosopher.hunger.get_hunger():3.0f}')
                self.status_bars.append(status_bar)

            while self.dead_count != len(self.philosophers):
                self.dead_count = 0

                for key, status_bar in enumerate(self.status_bars):
                    philosopher = self.philosophers[key]
                    if philosopher.is_alive():
                        if philosopher.is_feasting():
                            status_bar.update(
                                status=f'{"eating":10}', hunger=f'{philosopher.hunger.get_hunger():3.0f}')
                        else:
                            status_bar.update(
                                status=f'{"thinking":10}', hunger=f'{philosopher.hunger.get_hunger():3.0f}')
                    else:
                        status_bar.update(status=f'{"ded X(":10}')
                        self.dead_count += 1


PHILOSOPHER_COUNT = 5


def main():
    # init five (5) 'forks' for the five philosophers
    forks = [Fork() for f in range(PHILOSOPHER_COUNT)]

    # init five (5) philosophers
    philosophers = [
        Philosopher(uuid=i,
                    forkLeft=forks[i % PHILOSOPHER_COUNT],
                    forkRight=forks[(i + 1) % PHILOSOPHER_COUNT])
        for i in range(PHILOSOPHER_COUNT)
    ]

    for philosopher in philosophers:
        philosopher.start()

    monitor = Monitor(philosophers=philosophers)
    monitor.start()


if __name__ == '__main__':
    main()
