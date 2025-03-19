import logging

from loan.loan_base import Loan
from asset.asset import Car


class FixedRateLoan(Loan):
    def rate(self):
        return self._rate

'''
!! rateDict in VariableRateLoan must at least include one item for 0:rate !!
For example: {0: 0.05, 10: 0.06} or {0: 0.05} are correct, but {3: 0.05} is a wrong input.
'''


class VariableRateLoan(Loan):
    def __init__(self, face, rateDict, startDate_str, endDate_str, asset):
        # Validates that the rate parameter is indeed a dict
        if isinstance(rateDict, dict):
            self._rateDict = rateDict
        else:
            logging.error('Input rateDict type is wrong')
            raise TypeError('Exception: Please input rateDict in dict')

        super(VariableRateLoan, self).__init__(face, rateDict, startDate_str, endDate_str, asset)

    '''
    a single summary statistics for variable rate loan: time weighted interest rate
    Sigma_t Rate(t) / # of months
    '''
    def rate(self):
        return sum([self.getRate(t) for t in range(1, self.term()+1)]) / self.term()

    def getRate(self, period):
        earliestPeriod = period
        # search the earliest period after which the rate is effective until 'period'
        while self._rateDict.get(earliestPeriod) is None:
            earliestPeriod -= 1
        return self._rateDict.get(earliestPeriod)


class AutoLoan(FixedRateLoan):
    def __init__(self, notional, rate, startDate_str, endDate_str, car):
        if isinstance(car, Car):
            self._car = car
        else:
            logging.error('Input car type is wrong')
            raise TypeError('Exception: Please input asset(car parameter) specifically in Car type.')
        super(AutoLoan, self).__init__(notional, rate, startDate_str, endDate_str, car)
