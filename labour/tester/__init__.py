from collections import namedtuple
Result = namedtuple("Result", "responses, duration")
from responses import Responses
from policies import policy_map
from client import Client
