from functools import reduce
from asset.asset import Car,HomeBase,Lamborghini,Lexus,PrimaryHome,VacationHome
from loan.loans import AutoLoan
from loan.mortgages import VariableMortgage,FixedMortgage
import logging
import datetime

# change input argument term to startDate_str, endDate_str
# replace all variables, self._term/self.term, with the function method, self.term()


def AddAmountTerm(total, added):
    return total + (added.term() * added.notional)


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
        return sum([1 for loan in self._loans if loan.balance(t) > 0])

    # Methods to calculate the Weighted Average Maturity (WAM) and Weighted Average Rate
    # (WAR) of the loans.

    def WAM(self):
        numerator = reduce(AddAmountTerm, self._loans, 0)
        return numerator / self.totalPrincipal()

    def WAR(self):
        numerator = reduce(lambda total, loan: total + (loan.rate() * loan.notional), self._loans, 0)
        return numerator / self.totalPrincipal()

    # get the total loan balance for a given period

    def balance(self,t):
        return sum([loan.balance(t) for loan in self._loans])
    # get the aggregate principal, interest, and total payment due in a given period.

    def principalDue(self, t):
        return sum([loan.principalDue(t) for loan in self._loans])

    def interestDue(self, t):
        return sum([loan.interestDue(t) for loan in self._loans])

    def paymentDue(self, t):
        return sum([loan.monthlyPayment(t) for loan in self._loans])

    # get the total loan principal.

    def totalPrincipal(self):
        return reduce(lambda total, loan: total + loan.notional, self._loans, 0)

    def totalInterest(self):
        return sum([loan.totalInterest() for loan in self._loans])

    def totalPayments(self):
        return sum([loan.totalPayment() for loan in self._loans])

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


