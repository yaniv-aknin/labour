"""Policies are endless iterators that yield one Behaviour at a time
from a weighted sequence of Behaviours. Each policy chooses the next
Behaviour to yield according to its own algorithm."""

import random

class Policy(object):
    "The base class for all Policies."
    def __init__(self, behaviours, child_numbers):
        self.behaviours = behaviours
        self.child_numbers = child_numbers
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration()

class Random(Policy):
    "Yield Behaviours at Random."
    def __init__(self, behaviours, child_numbers):
        super(Random, self).__init__(behaviours, child_numbers)
        # NOTE: reseed our RNG after we inherited a seed from the parent
        random.seed()
    def next(self):
        return random.choice(self.behaviours)

class Repeat(Policy):
    """Yield Behaviours in the same order they appear in the behaviour
    sequence with which the class was initialized. The Repeat policy
    receives the number of the child process in which it is running
    and the total number of processes running in parallel. This
    information is used to roll the behaviour sequence thus that each
    child will start at a separate index in the sequence."""
    def __init__(self, behaviours, child_numbers):
        super(Repeat, self).__init__(behaviours, child_numbers)
        total_behaviours = len(self.behaviours)
        per_child_offset = total_behaviours / child_numbers.total
        current_child_offset = child_numbers.current * per_child_offset
        self.behaviours = (self.behaviours[current_child_offset:] +
                           self.behaviours[:current_child_offset])
    def __iter__(self):
        while True:
            for beheaviour in self.behaviours:
                yield beheaviour

policy_map = dict((policy.__name__, policy)
                  for policy in Policy.__subclasses__())
