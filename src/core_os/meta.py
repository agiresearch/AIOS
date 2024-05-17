from enum import Enum

class StepType(Enum):
    PROCESS = 'process'
    DECISION = 'decision'
    TERMINAL = 'terminal'