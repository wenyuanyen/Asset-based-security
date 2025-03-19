import numpy_financial as npf
from functools import reduce


class Tranche(object):
    def __init__(self, notional, rate, subordination):
        self._notional = notional
        self._rate = rate
        self._subordination = subordination
        # time: amount
        self.pastPrincipalPayment = {0: 0.0}
        self.pastInterestPayment = {0: 0.0}
        self.pastNotionalBalance = {0: notional}
        self.interestShortfall = {0: 0.0}
        self.principalShortfall = {0: 0.0}

    @property
    def notional(self):
        return self._notional

    @notional.setter
    def notional(self, i_notional):
        self._notional = i_notional

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, i_rate):
        self._rate = i_rate

    @property
    def subordination(self):
        return self._subordination

    @subordination.setter
    def subordination(self, i_subordination):
        self._subordination = i_subordination

    def IRR(self):
        cashFlows = []
        #print('>>>' + str(len(self.pastPrincipalPayment.items())))
        #print('>>>' + str(len(self.pastInterestPayment.items())))

        # principals
        for period, payment in self.pastPrincipalPayment.items():
            if period == 0:
                cashFlows.insert(period, -self.notional)
            else:
                cashFlows.insert(period, payment)

        # interests
        for period, payment in self.pastInterestPayment.items():
            cashFlows[period] += payment

        return npf.irr(cashFlows) * 12

    def DIRR(self):
        # in basis point
        return (self._rate - self.IRR()) * 100 * 100

    def AL(self):
        # if the tranche is not paid down
        tol = 10 ** -4
        lastPeriod = max(self.pastNotionalBalance.keys())
        if self.pastNotionalBalance.get(lastPeriod) > tol:
            return None
        else:
            return reduce(lambda total, item: total + (item[0] * item[1]), self.pastPrincipalPayment.items(), 0) / self.notional




