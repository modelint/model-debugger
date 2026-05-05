""" mdb_types.py -- Temporary home for mdb types while debugging """

# System
from typing import Union
from collections import namedtuple
from enum import Enum

Interaction = namedtuple('mdb_Interaction', 'direction action name source target parameters')

class ActionType(Enum):
    SIGNAL_INSTANCE = "signal instance"
    EXTERNAL_EVENT = "external event"

class Direction(Enum):
    STIMULUS = "stimulus"
    RESPONSE = "response"

class SuspendStatus(Enum):
    """
    Reasons why the system has stopped running
    """
    MONITOR_TRIPPED = "MONITOR_TRIPPED"  # An monitored condition or response was detected
    TERMINAL_CONDITION = "TERMINAL_CONDITION"  # The system has entered a terminal state