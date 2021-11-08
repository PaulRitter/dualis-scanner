from enum import Enum

DUALIS_URL = "https://dualis.dhbw.de/"
WINDOWOPEN_TIMEOUT = 10


class STATUSCODE(Enum):
    OK = 0
    INVALID_LOGIN = -1
    CRASH = -2