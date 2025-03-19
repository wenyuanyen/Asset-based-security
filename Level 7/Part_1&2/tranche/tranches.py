from tranche.tranche_base import Tranche


class StandardTranche(Tranche):

    # input subordination in numbers:
    # the larger the number, the more subordinated the tranche (can be any real number)

    def __init__(self, notional, rate, subordination):
        super(StandardTranche, self).__init__(notional, rate, subordination)
        self.period = 0

    def increaseTimePeriod(self):
        self.period += 1

    def makePrincipalPayment(self, principalPayment, principalDue):
        # Allowed being called once for a given time period
        if self.pastPrincipalPayment.get(self.period) is not None:
            raise ValueError('Current period principal payment has been made.')
        # Record the principal payment
        if self.pastNotionalBalance.get(self.period-1) <= 0:
            raise ValueError('The notional has been paid up.')
        else:
            self.pastPrincipalPayment[self.period] = principalPayment

            # Record shortfall
            if principalPayment < principalDue:
                self.principalShortfall[self.period] = principalDue - principalPayment
            else:
                self.principalShortfall[self.period] = 0

    def makeInterestPayment(self, interestPayment):
        # Allowed being called once for a given time period
        if self.pastInterestPayment.get(self.period) is not None:
            raise ValueError('Current period interest payment has been made.')
        # Record the interest payment
        if self.interestDue() <= 0:
            raise ValueError('Current interest due has been paid up.')
        else:
            self.pastInterestPayment[self.period] = interestPayment

            # Record shortfall
            if interestPayment < self.interestDue():
                self.interestShortfall[self.period] = self.interestDue() - interestPayment
            else:
                self.interestShortfall[self.period] = 0

    def notionalBalance(self):
        bal = self._notional - sum(self.pastPrincipalPayment.values()) #+ sum(self.interestShortfall.values())
        if bal < 0:
            raise ValueError('Notional balance calculation is wrong.')
        self.pastNotionalBalance[self.period] = bal
        return self.pastNotionalBalance.get(self.period)

    def interestDue(self):
        return self.pastNotionalBalance.get(self.period-1) * self._rate / 12 + \
               self.interestShortfall.get(self.period-1)

    def reset(self):
        self.period = 0


