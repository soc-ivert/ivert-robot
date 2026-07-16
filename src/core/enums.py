from enum import Enum  

class RobotState(Enum):
    SLEEPING = "sleeping"
    GREETING = "greeting"
    WAITING = "waiting"
    THINKING = "thinking"
    SPEAKING = "speaking"
    
    