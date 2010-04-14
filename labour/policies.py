import random

class Policy(object):
    def __init__(self, behaviours, child_numbers):
        self.behaviours = behaviours
        self.child_numbers = child_numbers
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration()

class Random(Policy):
    def __init__(self, behaviours, child_numbers):
        super(Random, self).__init__(behaviours, child_numbers)
        # NOTE: reseed our RNG after we inherited a seed from the parent
        random.seed()
    def next(self):
        return random.choice(self.behaviours)

class Repeat(Policy):
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

policies = dict((policy.__name__, policy)
                for policy in Policy.__subclasses__())
