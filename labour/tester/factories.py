"""An assortment of preconfigured client factories that represent "turnkey"
clients. This is particularly useful for a CLI based application that would
like to allow the user to select one or more preconfigured test patterns
(including Behaviours, Policy, etc)."""

import httplib

from ..behaviours import *
from policies import *
from client import Client

class TestFactory(object):
    def __init__(self, description, *behaviour_tuples, **kwargs):
        self.description = description
        self.behaviour_tuples = behaviour_tuples
        self.kwargs = kwargs
    def __call__(self):
        return Client.from_parameters(*self.behaviour_tuples, **self.kwargs)

Plain = TestFactory(
    "Endless sequence of 99 HTTP OK and 1 HTTP Not Found (404)",
    (PlainResponse(), 99),
    (PlainResponse(status=httplib.NOT_FOUND), 1),
    policy=Repeat
)

LightSleep = TestFactory(
    "Random choice of 99% HTTP OK and 1% 0.5 second sleep",
    (PlainResponse(), 99),
    (Sleeping(sleep_duration=0.5), 1),
)

HeavySleep = TestFactory(
    "Random choice of 95% HTTP OK and 5% 2 second sleep",
    (PlainResponse(), 95),
    (Sleeping(sleep_duration=2), 5),
)

SIGSEGV = TestFactory(
    "50/50 chance of HTTP OK or SIGSEGV",
    (PlainResponse(), 50),
    (SIGSEGV(), 50),
)

test_factory_map = dict((name, obj) for name, obj in globals().iteritems()
                        if isinstance(obj, TestFactory))
