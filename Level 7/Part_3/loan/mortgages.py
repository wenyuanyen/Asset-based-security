from loan.loans import VariableRateLoan, FixedRateLoan
from asset.asset import HomeBase
import logging


# change input argument term to startDate_str, endDate_str
# replace all variables, self._term/self.term, with the function method, self.term()

class MortgageMixin(object):
    def __init__(self, notional, rate, startDate_str, endDate_str, home):
        if not isinstance(home, HomeBase):
            logging.error('Input home type is wrong')
            raise TypeError('Exception: Please input asset(home parameter) specifically in HomeBase type.')

        super(MortgageMixin, self).__init__(notional, rate, startDate_str, endDate_str, home)

    def PMI(self, period):
        loanToValue = super(MortgageMixin, self).balance(period) / self.asset.initialValue
        if loanToValue > 0.8:
            return 0.000075 * self.notional
        else:
            return 0

    def monthlyPayment(self, period):
        return super(MortgageMixin, self).monthlyPayment(period) + self.PMI(period)

    def principalDue(self, period):
        return super(MortgageMixin, self).principalDue(period) - self.PMI(period)

    def principalDueRecursive(self, period):
        return super(MortgageMixin, self).principalDueRecursive(period) - self.PMI(period)

    def totalInterest(self):
        totalPMI = 0
        for i in range(1, self.term() + 1):
            totalPMI += self.PMI(i)
        return super(MortgageMixin, self).totalInterest() - totalPMI


class VariableMortgage(MortgageMixin, VariableRateLoan):
    pass


class FixedMortgage(MortgageMixin, FixedRateLoan):
    pass