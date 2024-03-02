from SAP_Operador.timers.timer import Timer

class TimerFactory:

    def createTimer(self, timerName):
        timers = {
            'Timer': Timer
        }
        return timers[timerName]()