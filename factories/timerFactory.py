from Ferramentas_Producao.timers.timer import Timer

class TimerFactory:

    def createTimer(self, timerName):
        timers = {
            'Timer': Timer
        }
        return timers[timerName]()