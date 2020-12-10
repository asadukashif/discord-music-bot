

class Time():
    def __init__(self, start: float = 0, paused_on: float = 0, paused_off: float = 0, compensation: float = 0, initial_seek: int = 0) -> None:
        self.start = start
        self.paused_on = paused_on
        self.paused_off = paused_off
        self.compensation = compensation
        self.initial_seek = initial_seek
