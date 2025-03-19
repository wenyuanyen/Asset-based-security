from functools import reduce
from asset.asset import Car,HomeBase,Lamborghini,Lexus,PrimaryHome,VacationHome
from loan.loans import AutoLoan
from loan.mortgages import VariableMortgage,FixedMortgage
import logging
import datetime
import random

# change input argument term to startDate_str, endDate_str
# replace all variables, self._term/self.term, with the function method, self.term()


class LoanPool(object):

    def __init__(self, loans):
        self._loans = loans

    # Generator
    def __iter__(self):
        for loan in self._loans:
            yield loan

    @property
    def loans(self):
        return self._loans

    @loans.setter
    def loans(self, loansList):
        self._loans = loansList

    # returns the number of ‘active’ loans. Active loans are loans that have a
    # balance greater than zero.

    def activeLoanCount(self, t):
        return sum(1 for loan in self._loans if loan.balance(t) > 0)

    # Methods to calculate the Weighted Average Maturity (WAM) and Weighted Average Rate
    # (WAR) of the loans.

    def WAM(self):
        numerator = reduce(lambda total, loan: total + (loan.term() * loan.notional), self._loans, 0)
        return numerator / self.totalPrincipal()

    def WAR(self):
        numerator = reduce(lambda total, loan: total + (loan.rate() * loan.notional), self._loans, 0)
        return numerator / self.totalPrincipal()

    # get the total loan balance for a given period
    def balance(self, t):
        return sum(loan.balance(t) for loan in self._loans)

    # get the aggregate principal, interest, and total payment due in a given period.
    def principalDue(self, t):
        return sum(loan.principalDue(t) for loan in self._loans)

    def interestDue(self, t):
        return sum(loan.interestDue(t) for loan in self._loans)

    def paymentDue(self, t):
        return sum(loan.monthlyPayment(t) for loan in self._loans)

    # get the total loan principal.

    def totalPrincipal(self):
        return reduce(lambda total, loan: total + loan.notional, self._loans, 0)

    def totalInterest(self):
        return reduce(lambda total, loan: total + loan.totalInterest(), self._loans, 0)

    def totalPayments(self):
        return reduce(lambda total, loan: total + loan.totalPayment(), self._loans, 0)

    def getWaterfall(self, period):
        return [self.principalDue(period), self.interestDue(period), self.paymentDue(period), self.balance(period)]

    @classmethod
    def createLoan(cls, loanType, assetName, assetValue, principal, rate, term):
        loanNameToClass = {
            'AutoLoan': AutoLoan,
            'FixedMortgage': FixedMortgage
        }

        assetNameToClass = {
            'Lamborghini': Lamborghini,
            'Lexus': Lexus,
            'VacationHome': VacationHome,
            'PrimaryHome': PrimaryHome,
            'Car': Car
        }

        assetCls = assetNameToClass.get(assetName)

        today = datetime.datetime.today()

        if assetCls:
            asset = assetCls(float(assetValue))
            loanCls = loanNameToClass.get(loanType)

            if loanCls:
                loan = loanCls(float(principal), float(rate),
                               datetime.datetime.strftime(today, '%Y-%m-%d'),
                               datetime.datetime.strftime(today + datetime.timedelta(days=int(term)*30), '%Y-%m-%d'),
                               asset)
                return loan
            else:
                logging.error('Invalid loan type entered.')
        else:
            logging.error('Invalid asset type entered.')

    def checkDefaults(self, period):

        if period in range(1, 11):
            prob = 0.0005
        elif period in range(11, 60):
            prob = 0.001
        elif period in range(60, 120):
            prob = 0.002
        elif period in range(120, 180):
            prob = 0.004
        elif period in range(180, 210):
            prob = 0.002
        else:
            prob = 0.001

        '''
        aggregate recovery value from all loans
        '''
        return reduce(lambda total, loan: total + loan.checkDefault(random.randint(0, int(1 / prob)-1), period),
                      self._loans, 0)


