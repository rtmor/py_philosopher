# author: Ryan T. Moran
# title: Dining-Philosophers
# date: 19 Mar 2021
# description: Python solution for the classic Dining-Philosophers problem.
#    Application implements hunger feature which depletes over time and
#    increments when access to forks is secured. A monitoring class is included
#    to track the status of all Philosophers, and makes use of the enlighten
#    library to handle the formating of this information to stdout in a neat
#    manner. Program will continue to run until all Philosophers die.

import threading
import enlighten
import random
import time
import math
import sys


# Fork is a threading.Lock() wrapper. Forks in this application
# serve as shared resources, and require a lock to possess.
class Fork(object):
    def __init__(self):
        self.__lock = threading.Lock()

    def acquire(self, blocking=True, timeout=None):
        return self.__lock.acquire(blocking)

    def release(self):
        self.__lock.release()


# Hunger is responsible for tracking the hunger level of a philosopher
# Allowing separate hunger instances per philosopher enables ability
# to assign unique hunger rates. All hunger starts at 100, and each iteration
# is assigned a new random rate at which the random quanty of hunger will be
# subtracted. Subclasses threading.Thead()
class Hunger(threading.Thread):
    def __init__(self, philosopher_id: int):
        self.active = True
        self.hunger = 100
        self.uuid = philosopher_id
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        # while philosopher's still active (hunger > 0)
        # determine random rate to subtract random quantity of hunger
        while self.active:
            random.seed()
            rate_of_starvation = float(random.randint(2, 5))
            qnt_of_starvation = float(random.randint(5, 15))

            self.deplete(qnt_of_starvation)
            time.sleep(rate_of_starvation)

    # fill is a helper function which adds a given amount to available hunger meter
    def fill(self, amount: int):
        hunger_level = self.hunger + amount
        self.hunger = 100.0 if hunger_level > 100.0 else hunger_level

    # deplete is a helper function which subtracts a given amount to available hunger meter
    def deplete(self, amount: int):
        hunger_level = self.hunger - amount
        self.hunger = 0.0 if hunger_level <= 0.0 else hunger_level

    def get_hunger(self):
        return self.hunger

    def starved(self):
        return self.hunger <= 0.0


# Philosopher class competes against other Philosophers for Fork resources.
# Each Philosopher is instantiated with references to both the Fork to his
# left and right, as well as a new Hunger object to measure hunger
# over time. If the philosospher's hunger reaches zero, he dies. The Philosopher
# class subclasses threading.Thread().
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

        # while phil hunger is greater than zero
        while not self.hunger.starved():
            self.ponder()       # waiting function to simulate Philosopher thought
            self.try_eat()      # Attempts to acquire access to shared Forks

        self.__clean_up()

    # ponder is a waiting function which sleeps for a period of 1 to 4 seconds
    def ponder(self):
        random.seed()
        time_in_thought = random.randint(1, 4)
        time.sleep(float(time_in_thought))

    # try_eat is responsible for acquiring a lock on the shared Forks
    def try_eat(self):
        self.forkLeft.acquire(blocking=True)    # be greedy

        # if right fork is unavailable, release left fork
        acquired = self.forkRight.acquire(blocking=False)
        if not acquired:
            self.forkLeft.release()
            return

        # start eating!
        # release fork resources when finished
        self.feast()                            # waiting function
        self.forkLeft.release()
        self.forkRight.release()

    # feast is accessible only with acquisition of both Forks
    def feast(self):
        # signal for monitoring process
        self.feasting = True

        # assign random value from 1-5 for time spent eating.
        random.seed()
        time_eating = float(random.randint(1, 5))

        # hunger meter filled proportional to the amount of time spent eating.
        # largest possible increase per session is 14.
        self.hunger.fill(14 * (time_eating / 5))
        time.sleep(time_eating)

        self.feasting = False

    # is_feasting is a getter for feasting indicator
    def is_feasting(self):
        return self.feasting

    def __clean_up(self):
        self.hunger.active = False


# Monitor is responsible for tracking and outputing status information
# related to the list of provided Philosophers. The class implements
# the enlighten context manager, which is responsible for handling the
# output and format of information to stdout.
#
# dead_count is the signal for monitoring the total number of exited
# Philosopher processes, and if whose value reaches the count of total
# Philosophers, will signal return to calling function.
class Monitor():
    def __init__(self, philosophers: list()):
        self.manager = enlighten.get_manager()
        self.philosophers = philosophers
        self.status_bars = list()   # list of all Philosophers status bars
        self.dead_count = 0         # term signal

    def start(self):
        # with enlighten.ContextManager()
        with self.manager:
            # instantiate status bar for each Philosopher passed in philosophers:[]Philosopher
            for philosopher in self.philosophers:
                status_format = '{philosopher}{fill}Status: {status}{fill} Hunger: {hunger}'
                status_bar = self.manager.status_bar(color='green',
                                                     status=f'{"thinking":10}',
                                                     hunger=f'{philosopher.hunger.get_hunger():3.0f}',
                                                     philosopher=f'Philosopher {philosopher.uuid}',
                                                     status_format=status_format)
                self.status_bars.append(status_bar)

            # while the count of exited Philosospher processes not equal to count of all Philosophers
            while self.dead_count != len(self.philosophers):
                self.dead_count = 0

                # update each status_bar with status of respective Philosopher
                for key, status_bar in enumerate(self.status_bars):
                    philosopher = self.philosophers[key]

                    # check if philosopher is still alive, otherwise report as ded
                    if philosopher.is_alive():
                        # if not feasting, then eating
                        if philosopher.is_feasting():
                            status_bar.update(
                                status=f'{"eating":10}', hunger=f'{philosopher.hunger.get_hunger():3.0f}')
                        else:
                            status_bar.update(
                                status=f'{"thinking":10}', hunger=f'{philosopher.hunger.get_hunger():3.0f}')
                    else:
                        status_bar.update(status=f'{"ded X(":10}')
                        self.dead_count += 1    # increment exited process count


# constant for count of Philosopher
PHILOSOPHER_COUNT = 5


def main():
    # initialize list of Forks() equal to PHILOSOPHER_COUNT.
    forks = [Fork() for f in range(PHILOSOPHER_COUNT)]

    # initialize list of Philosopher() equal to PHILOSOPHER_COUNT.
    # use (mod) to assign each Philosopher the two Forks to
    # to their left and right.
    philosophers = [
        Philosopher(uuid=i,
                    forkLeft=forks[i % PHILOSOPHER_COUNT],
                    forkRight=forks[(i + 1) % PHILOSOPHER_COUNT])
        for i in range(PHILOSOPHER_COUNT)
    ]

    # start each Philosopher thread
    for philosopher in philosophers:
        philosopher.start()

    print(f"The {PHILOSOPHER_COUNT} Philosophers Begin Dining")

    # instantiate and start the monitoring task responsible for tracking
    # Philosopher status and output/formatting to stdout
    monitor = Monitor(philosophers=philosophers)
    monitor.start()


if __name__ == '__main__':
    main()
