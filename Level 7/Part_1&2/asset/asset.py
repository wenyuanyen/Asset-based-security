class Asset(object):
    def __init__(self, initialValue):
        self._initialValue = float(initialValue)

    def annualDepr(self, period):
        raise NotImplementedError()

    def monthlyDepr(self, period):
        return self.annualDepr(period)/12

    def value(self, period):
        return self._initialValue * (1 - self.monthlyDepr(period)) ** period

    '''
    The setter/getter using property methods
    '''
    @property
    def initialValue(self):
        return self._initialValue

    @initialValue.setter
    def initialValue(self, initialValue):
        self._initialValue = initialValue


class Car(Asset):
    def annualDepr(self, period):
        return 0


class HomeBase(Asset):
    def annualDepr(self, period):
        return 0


class Lamborghini(Car):
    def annualDepr(self, period):
        return 0.10


class Lexus(Car):
    def annualDepr(self, period):
        return 0.05


class PrimaryHome(HomeBase):
    def annualDepr(self, period):
        return 0.05


class VacationHome(HomeBase):
    def annualDepr(self, period):
        return 0.025









