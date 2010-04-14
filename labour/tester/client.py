import logging
import time
import os

from ..http_hit import hit
from multicall import multicall
from . import Responses
from . import Result
import policies

LOGGER = logging.getLogger('client')

class Client(object):
    def __init__(self, host='localhost', port=8000, timeout_seconds=30,
                 policy=policies.Random):
        self.host = host
        self.port = port
        self.timeout_seconds = 30
        self.responses = Responses()
        self.behaviours = []
        self.policy = policy
    @classmethod
    def from_behaviour_tuples(cls, *behaviour_tuples, **kwargs):
        result = cls(**kwargs)
        for behaviour, weight in behaviour_tuples:
            result.add(behaviour, weight)
        return result
    @property
    def base(self):
        return 'http://%s:%s' % (self.host, self.port,)
    def add(self, behaviour, weight):
        self.behaviours.extend([behaviour]*weight)
    def divide_iterations(self, iterations, number_processes):
        if iterations < number_processes or iterations % number_processes != 0:
            raise ValueError('can not divide %d iterations between %d processes')
        return iterations / number_processes
    def execute(self, iterations=1, number_processes=1):
        child_iterations = self.divide_iterations(iterations, number_processes)
        LOGGER.info('generating %s requests using %d processes' %
                    (iterations, number_processes))
        start_time = time.time()
        results = multicall(self._execute, (child_iterations,),
                            how_many=number_processes, pass_child_numbers=True)
        duration = time.time() - start_time
        self.responses = sum(results, self.responses)
        LOGGER.info('finished all requests')
        return Result(self.responses, duration)
    def _execute(self, iterations, child_numbers):
        # NOTE: this will run in a child process
        global LOGGER
        LOGGER = logging.getLogger('client.%d' % (os.getpid(),))
        LOGGER.debug('running %d iterations' % (iterations,))
        responses = Responses()
        behaviour_iterator = iter(self.policy(self.behaviours, child_numbers))
        for iteration in xrange(iterations):
            # HACK: use proper url joining
            behaviour = behaviour_iterator.next()
            result = hit(self.base + '/' + str(behaviour),
                         timeout=behaviour.timeout)
            if behaviour.is_expected_response(result):
                responses.success()
            else:
                responses.failure(result)
        return responses
