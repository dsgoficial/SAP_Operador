from datetime import date, time, datetime
from qgis.core import QgsSettings


class UserHistoric:

    # TODO UserHistoric should be a singleton
    def __init__(self):
        self.s = QgsSettings()
        variables = ['dateLastAcess', 'sThisSession', 'fThisSession',
                     'workTime', 'idleTime',
                     'greatWorkTime', 'greatIdleTime', 'tmpGreatWorkTime',
                     'tmpGreatIdleTime', 'idleSince', 'timeFirstAcess']
        dateLastAcess = self.s.value("pomodoro/dateLastAcess", None)
        self.lastStatus = True
        self.tick = 1
        # TODO after implementing a singleton, date.today() should be updated inside init
        if dateLastAcess == date.today().isoformat():
            self.vars = {x: self.s.value(f"pomodoro/{x}", 0)
                         for x in variables}
        else:
            self.restartVariables()
            self.vars = {x: self.s.value(f"pomodoro/{x}", 0)
                         for x in variables}
            self.vars['timeFirstAcess'] = datetime.time(
                datetime.now()).isoformat(timespec='minutes')
            self.s.setValue('pomodoro/timeFirstAcess', self.vars['timeFirstAcess'])
            self.s.setValue('pomodoro/dateLastAcess', date.today().isoformat())

    # TODO setValue should be called from an unique function which receives the param name
    def updateSucess(self):
        self.vars['sThisSession'] = int(self.vars['sThisSession']) + self.tick
        self.s.setValue('pomodoro/sThisSession', self.vars['sThisSession'])

    def updateFail(self):
        self.vars['fThisSession'] = int(self.vars['fThisSession']) + self.tick
        self.s.setValue('pomodoro/fThisSession', self.vars['fThisSession'])

    def updateWorkTime(self):
        self.vars['workTime'] = int(self.vars['workTime']) + self.tick
        self.s.setValue('pomodoro/workTime', self.vars['workTime'])
        self.vars['idleSince'] = 0
        if self.lastStatus:
            self.vars['tmpGreatWorkTime'] = int(
                self.vars['tmpGreatWorkTime']) + self.tick
        else:
            self.vars['tmpGreatWorkTime'] = 0
        self.lastStatus = True
        self.updatelongestWorkTime()

    def updateIdleTime(self):
        # TODO idleSince not updating correctly
        self.vars['idleTime'] = int(self.vars['idleTime']) + self.tick
        self.s.setValue('pomodoro/idleTime', self.vars['idleTime'])
        if not self.lastStatus:
            self.vars['tmpGreatIdleTime'] = int(
                self.vars['tmpGreatIdleTime']) + self.tick
            self.vars['idleSince'] = self.vars['tmpGreatIdleTime']
        else:
            self.vars['tmpGreatIdleTime'] = 0
        self.lastStatus = False
        self.updatelongestWorkTime()

    def updatelongestWorkTime(self):
        tmpGreatWorkTime, greatWorkTime, tmpGreatIdleTime, greatIdleTime = [
            int(self.vars['tmpGreatWorkTime']), int(
                self.vars['greatWorkTime']),
            int(self.vars['tmpGreatIdleTime']), int(self.vars['greatIdleTime'])
        ]
        if tmpGreatWorkTime > greatWorkTime:
            self.vars['greatWorkTime'] = tmpGreatWorkTime
            self.s.setValue('pomodoro/greatWorkTime',
                            self.vars['greatWorkTime'])
        if tmpGreatIdleTime > greatIdleTime:
            self.vars['greatIdleTime'] = tmpGreatIdleTime
            self.s.setValue('pomodoro/greatIdleTime',
                            self.vars['greatIdleTime'])
        self.s.setValue('pomodoro/dateLastAcess', date.today().isoformat())

    def restartVariables(self):
        variables = ['dateLastAcess', 'sThisSession', 'fThisSession',
                     'workTime', 'idleTime',
                     'greatWorkTime', 'greatIdleTime', 'tmpGreatWorkTime',
                     'tmpGreatIdleTime', 'idleSince', 'timeFirstAcess']
        for item in variables:
            self.s.setValue(f'pomodoro/{item}', 0)
