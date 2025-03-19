# Loan Modeling 101
from asset.asset import Asset
import logging
import datetime


# input date in 'YYYY-MM-DD'
# add term method
# replace all variables, self._term/self.term, with the function method, self.term()

def Memoize(fn):
    memo = {}

    def helper(*args):
        if args not in memo:
            memo[args] = fn(*args)
        return memo[args]
    return helper


class Loan(object):
    def __init__(self, notional, rate, startDate_str, endDate_str, asset):
        self._notional = float(notional)
        self._rate = rate  # can be float or None (VariableRateLoan)
        # self._term = int(term)
        self._startDate = datetime.datetime.strptime(startDate_str, '%Y-%m-%d')
        self._endDate = datetime.datetime.strptime(endDate_str, '%Y-%m-%d')
        if isinstance(asset, Asset):
            self._asset = asset
        else:
            logging.error('Input asset class type is wrong.')
            raise TypeError('Exception: Please input asset in Asset.')
        self.defaultFlag = 0
        self.defaultPeriod = None

    @classmethod
    def calcMonthlyPmt(cls, face, rate, term):
        logging.debug('Calculating monthly payment...')
        return rate * face / (1 - (1 + rate) ** (-term))

    @classmethod
    def calcBalance(cls, face, rate, term, period):
        logging.debug('Calculating loan balance...')
        return face * (1 + rate) ** period - Loan.calcMonthlyPmt(face, rate, term) * ((1 + rate) ** period - 1) / rate

    @staticmethod
    def monthlyRate(annualRate):
        return annualRate / 12

    @staticmethod
    def annualRate(monthlyRate):
        return monthlyRate * 12

    '''
    The setter/getter using property methods
    '''

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

    # @property
    # def term(self):
    # return self._term

    # @term.setter
    # def term(self, i_term):
    # self._term = i_term

    @property
    def startDate(self):
        return self._startDate

    @startDate.setter
    def startDate(self, i_startDate):
        self._startDate = i_startDate

    @property
    def endDate(self):
        return self._endDate

    @endDate.setter
    def endDate(self, i_endDate):
        self._endDate = i_endDate

    @property
    def asset(self):
        return self._asset

    @asset.setter
    def asset(self, i_asset):
        if isinstance(i_asset, Asset):
            self._asset = i_asset
        else:
            logging.error('Input asset class type is wrong.')
            raise TypeError('Exception: Please input asset in Asset.')

    # if not over-ridden by derived class
    def getRate(self, period):
        return self._rate

    # replace self._rate with self.getRate(period)
    def monthlyPayment(self, period):
        if self.defaultFlag == 1:
            if period >= self.defaultPeriod:
                return 0
        elif period in range(1, self.term() + 1):
            return Loan.calcMonthlyPmt(self._notional, Loan.monthlyRate(self.getRate(period)), self.term())
        else:
            logging.info('Input period is greater than term')
            return 0

    # modified to sum variable monthly payment
    def totalPayment(self):
        sumPayment = 0
        for t in range(1, self.term() + 1):
            sumPayment += self.monthlyPayment(t)
        return sumPayment

    def totalInterest(self):
        return self.totalPayment() - self._notional

    # returns the loan term (in months) from the two dates
    def term(self):
        diff = self._endDate - self._startDate
        return round(diff.days / 30)

    '''
    formulas-based
    '''

    # replace self._rate with self.getRate(period)
    @Memoize
    def balance(self, period):
        if self.defaultFlag == 1:
            if period >= self.defaultPeriod:
                return 0
        elif period in range(0, self.term() + 1):  # enable showing t = 0 balance
            return Loan.calcBalance(self._notional, Loan.monthlyRate(self.getRate(period)), self.term(), period)
        else:
            return 0

    # replace self._rate with self.getRate(period)
    @Memoize
    def interestDue(self, period):
        if self.defaultFlag == 1:
            if period >= self.defaultPeriod:
                return 0
        elif period in range(1, self.term() + 1):
            return self.balance(period - 1) * Loan.monthlyRate(self.getRate(period))
        else:
            return 0

    # input period as the parameter in self.monthlyPayment()
    @Memoize
    def principalDue(self, period):
        if period in range(1, self.term() + 1):
            return self.monthlyPayment(period) - self.interestDue(period)
        else:
            return 0

    '''
    recursive version
    only balanceRecursive has logging because other 2 used it as well.
    '''

    @Memoize
    def balanceRecursive(self, period):
        if period == 0:
            return self._notional
        else:
            # logging.warn('Recursive functions will take some time...please wait')
            return self.balanceRecursive(period - 1) - self.principalDueRecursive(period)

    # replace self._rate with self.getRate(period)
    @Memoize
    def interestDueRecursive(self, period):
        # logging.warn('Recursive functions will take a long time...')
        return self.balanceRecursive(period - 1) * Loan.monthlyRate(self.getRate(period))

    # input period as the parameter in self.monthlyPayment()
    @Memoize
    def principalDueRecursive(self, period):
        # logging.warn('Recursive functions will take a long time...')
        return self.monthlyPayment(period) - self.interestDueRecursive(period)

    '''
    Asset/Equity
    '''

    def recoveryValue(self, period):
        recoveryMultiplier = 0.6
        return self._asset.value(period) * recoveryMultiplier

    def equity(self, period):
        return self._asset.value(period) - self.balance(period)

    def checkDefault(self, randNum, period):
        if self.defaultFlag == 1:  # has been defaulted
            return 0
        elif randNum == 0:  # is defaulting at now
            self.defaultFlag = 1
            self.defaultPeriod = period
            return self.recoveryValue(period)
        else:  # is not defaulting at now
            return 0



