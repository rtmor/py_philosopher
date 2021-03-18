import threading
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
        self.uid = philosopher_id
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
        self.hunger = 100 if hunger_level > 100 else hunger_level

    def deplete(self, amount: int):
        hunger_level = self.hunger - amount
        self.hunger = 0 if hunger_level <= 0 else hunger_level

    def get_hunger(self):
        return self.hunger

    def starved(self):
        return self.hunger <= 0


class Philosopher(threading.Thread):
    def __init__(self, uid: int, forkLeft: Fork, forkRight: Fork):
        self.uid = uid
        self.forkLeft = forkLeft
        self.forkRight = forkRight
        self.feasting = False
        self.hunger = Hunger(philosopher_id=uid)

        threading.Thread.__init__(self)

    def run(self):
        self.hunger.start()

        while not self.hunger.starved():
            self.ponder()
            self.try_eat()

        self.__clean_up()

    def ponder(self):
        time_in_thought = random.randint(1, 8)
        time.sleep(float(time_in_thought))

    def try_eat(self):
        acquired = self.forkLeft.acquire(blocking=False)
        if not acquired:
            return

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

        time_eating = float(random.randint(1, 10))
        self.hunger.fill(20 * (time_eating / 10))
        time.sleep(time_eating)

        self.feasting = False

    def is_feasting(self):
        return self.feasting

    def __clean_up(self):
        self.hunger.active = False


class Monitor(threading.Thread):
    def __init__(self, philosophers: Philosopher):
        self.active = True
        self.philosphers = philosophers
        self.dead_count = 0
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        while not self.philosphers[0].is_alive():
            time.sleep(.25)

        while self.dead_count != len(self.philosphers):
            self.dead_count = 0
            output = str()

            for philosopher in self.philosphers:
                prefix = f'philosopher {philosopher.uid}'
                if philosopher.is_alive():
                    # hunger = f'|{"#" * (40//philosopher.hunger.get_hunger())}'
                    output += f'{prefix} Hunger: {philosopher.hunger.get_hunger()}'
                    if philosopher.is_feasting():
                        output += f' - eating'
                    else:
                        output += f' - thinking'
                else:
                    self.dead_count += 1
                    output += f'{prefix} ded X('

                output += '\n'

            print(output)
            time.sleep(.20)


PHILOSOPHER_COUNT = 5


def main():
    # init five (5) 'forks' for the five philosophers
    forks = [Fork() for f in range(PHILOSOPHER_COUNT)]

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

    monitor = Monitor(philosophers)
    monitor.start()


if __name__ == '__main__':
    main()
