from enum import Enum

class SentioRoom:
    def __init__(self, index, name):
        self.index = index;
        self.name = name;

    def __str__(self):
        return "{0} - {1}".format(self.index, self.name)



class SentioDeviceType(Enum):
    CCU208 = 1
    DHW201 = 2

class SentioCMVVentilationState(Enum):
    STOPPED = 0
    UNOCCUPIED = 1
    ECONOMY = 2
    COMFORT = 3
    BOOST = 4
    BLOCKED_STOPPED = 5
    BLOCKED_UNOCCUPIED = 6
    BLOCKED_ECONOMY = 7
    BLOCKED_COMFORT = 8
    BLOCKED_BOOST = 9
    FAILURE = 10
    MAINTENANCE = 11

class SentioHeatingStates(Enum):
    IDLE = 1
    HEATING = 2 
    COOLING = 3
    BLOCKED_HEATING = 4 
    BLOCKED_COOLING = 5

class SentioRoomMode(Enum):
    SCHEDULE = 0
    MANUAL = 1
    
class SentioRoomModeSetting(Enum):
    RM_NONE = 0
    RM_TEMPORARY = 1
    RM_VACATION_AWAY = 2
    RM_ADJUST = 3