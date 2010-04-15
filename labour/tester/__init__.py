"""This package contains code pertaining to issuing HTTP requests
towards the tested WSGI Server, matching the resulting HTTP responses
with the expected responses and logging an aggregating of this match
for further reporting or inspection by some other piece of code."""

from collections import namedtuple
Result = namedtuple("Result", "responses, duration")
from responses import Responses
from policies import policy_map
from client import Client
import factories
import cli
