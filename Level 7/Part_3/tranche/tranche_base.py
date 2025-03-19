import numpy_financial as npf
from functools import reduce
import numpy as np


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
        cashFlows = np.array([])
        #cashFlows = []

        # principal payments
        for period, payment in self.pastPrincipalPayment.items():
            if period == 0:
                cashFlows = np.insert(cashFlows, period, -self.notional)
                #cashFlows.insert(period, -self.notional)
            else:
                cashFlows = np.insert(cashFlows, period, payment)
                #cashFlows.insert(period, payment)

        # interests payments
        for period, payment in self.pastInterestPayment.items():
            cashFlows[period] += payment

        return npf.irr(cashFlows) * 12  # annualized IRR

    # in basis point
    def DIRR(self):
        if not np.isclose(self._rate, self.IRR()):
            return (self._rate - self.IRR()) * 100 * 100
        else:
            # if all cash flows are paid timely and fully, rate should = IRR
            # tiny difference is due to numpy.irr rounding error
            return 0

    def AL(self):
        # if the tranche is not paid down (tol is remaining balance)
        tol = 1  # should have been 0 but use 1 to prevent floating/rounding issues
        lastPeriod = max(self.pastNotionalBalance.keys())
        if self.pastNotionalBalance.get(lastPeriod) > tol:
            return 'Inf'
        else:
            # items are (key,value) = (time period, principal payment)
            return reduce(lambda total, item: total + (item[0] * item[1]),
                          self.pastPrincipalPayment.items(), 0) / self.notional




