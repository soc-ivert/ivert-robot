from enum import Enum, auto  

class RobotState(Enum):
    SLEEPING = "sleeping"
    GREETING = "greeting"
    WAITING = "waiting"
    THINKING = "thinking"
    SPEAKING = "speaking"
    
    