"""A bare-bones but effective way to run a target callable in parallel
using multiple processes.

POSIX specific.

The reason I opted to use this rather than 'import multiprocessing' is
that multiprocessing uses threads to listen in the background for
results returning on kids' sockets. If possible, I would rather not
initialize the threading mechanism at all* and gain a bit more
performance for my children.

* initializing the threading mechanism calls ceval.c:PyEval_InitThreads,
which incurs overhead for many future operations; avoiding threads
altogether can gain visible performance increases, especially when
doing locking intensive operations
"""

__author__ = 'Yaniv Aknin (yaniv@aknin.name)'

import os
from select import select
from cPickle import dumps, loads

# NOTE: makes waitpid() below more readable
NO_OPTIONS = 0

class ExceptionsRaisedInChildren(Exception):
    pass

def multicall(target, args=None, kwargs=None, how_many=None,
              permit_exceptions=False):
    args = args or []
    kwargs = kwargs or {}

    pids, pipes = fork_children(target, args, kwargs, how_many)
    raw_results = read_raw_results_in_parallel(pipes)
    # RANT: I used to think Unix terminology is funny...
    #        as I get older, 'reap dead children' gets less funny.
    reap_dead_children(pids)
    return process_results(raw_results, permit_exceptions)

def fork_children(target, args, kwargs, how_many):
    pids = []
    pipes = {}
    for iterator in xrange(how_many):
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            exec_child_and_never_return(write_fd, target, args, kwargs)
        os.close(write_fd)
        pids.append(pid)
        pipes[read_fd] = []
    return pids, pipes

def read_raw_results_in_parallel(pipes):
    raw_results = []
    while pipes:
        read_fds, dummy_write_fds, dummy_exceptional_fds = select(pipes, [], [])
        for read_fd in read_fds:
            data = os.read(read_fd, 4096)
            if not data:
                raw_results.append(pipes.pop(read_fd))
            else:
                pipes[read_fd].append(data)
    return raw_results

def reap_dead_children(pids):
    while pids:
        waitable_pid = pids.pop()
        waited_pid, sts = os.waitpid(waitable_pid, NO_OPTIONS)
        assert waitable_pid == waited_pid

def process_results(raw_results, permit_exceptions):
    results = [loads("".join(raw_result)) for raw_result in raw_results]
    exceptions = [result for result in results if isinstance(result, Exception)]
    if exceptions:
        if not permit_exceptions:
            raise ExceptionsRaisedInChildren(exceptions)
    return results

def exec_child_and_never_return(write_fd, target, args, kwargs):
    try:
        try:
            result = target(*args, **kwargs)
        except Exception, error:
            result = error
        # NOTE: the following line may block if the parent buffer is full, that's cool with us
        os.write(write_fd, dumps(result))
    finally:
        # NOTE: no matter what, the child must exit here
        os._exit(0)

def test():
    def plain_target(*args, **kwargs):
        return args
    def random_sleeps():
        from time import sleep
        from random import random
        sleep(random())
        return 42
    def large_output():
        return 'a' * 2**20
    PROCESSES = 32
    assert multicall(plain_target, (1,2,3), how_many=PROCESSES) == [(1,2,3)] * PROCESSES
    assert multicall(random_sleeps, how_many=PROCESSES) == [42] * PROCESSES
    assert multicall(large_output, how_many=PROCESSES) == ['a' * 2**20] * PROCESSES
if __name__ == '__main__':
    test()
