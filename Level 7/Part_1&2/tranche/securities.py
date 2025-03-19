from tranche.tranches import StandardTranche
import numpy


def rating(dirr):
    ratingTable = {
        0.06: 'Aaa',
        0.67: 'Aa1',
        1.3: 'Aa2',
        2.7: 'Aa3',
        5.2: 'A1',
        8.9: 'A2',
        13: 'A3',
        19: 'Baa1',
        27: 'Baa2',
        46: 'Baa3',
        72: 'Ba1',
        106: 'Ba2',
        143: 'Ba3',
        183: 'B1',
        231: 'B2',
        311: 'B3',
        2500: 'Caa',
        10000: 'Ca'
    }
    bps = numpy.array(list(ratingTable.keys()))
    if dirr < 0.06:
        return 'Aaa'
    else:
        return ratingTable.get(bps[bps <= dirr].max())


def doWaterfall(loanPool, structuredSecurities):
    t = 1
    asset = []
    liability = []
    while loanPool.activeLoanCount(t) > 0:
        structuredSecurities.increaseTimePeriod()
        structuredSecurities.makePayments(loanPool.paymentDue(t), loanPool.principalDue(t))
        liability.append(structuredSecurities.getWaterfall(t))
        asset.append(loanPool.getWaterfall(t))
        t += 1

    for trancheCompleted in structuredSecurities:
        if trancheCompleted.AL():
            ALMsg = f' Average Life {trancheCompleted.AL(): .2f} months;'
        else:
            ALMsg = f' Average Life is infinite;'

        print(f'Tranche {trancheCompleted.subordination} has IRR {trancheCompleted.IRR()*100: .2f}%; '
              f' Reduction in Yield {trancheCompleted.DIRR(): .2f} bps;'+ ALMsg +
              f' Letter Rating {rating(trancheCompleted.DIRR())}.')

    return asset, liability, structuredSecurities.reserveAccount


class StructuredSecurities(object):
    def __init__(self, totalNotional):
        self._tranches = []
        self._totalNotional = totalNotional
        self.method = 'Sequential'
        self.reserveAccount = 0
        self.AccuPrincipalCollections = 0
        self.waterfalls = []

    # Generator
    def __iter__(self):
        for tranche in self._tranches:
            yield tranche

    def addTranche(self, trancheClassName, percentOfNotional, rate, subordination):
        trancheNameToClass = {
            'StandardTranche': StandardTranche
        }

        newTrancheCls = trancheNameToClass.get(trancheClassName)

        if newTrancheCls:
            newTranche = newTrancheCls(percentOfNotional/100 * self._totalNotional, rate, subordination)
            self._tranches.append(newTranche)

        # sort the tranche list by subordination: higher priority put first.
        self._tranches = sorted(self._tranches, key=lambda tranche: tranche.subordination, reverse=False)

    # flag = 'Sequential' or 'ProRata'
    def mode(self, flag):
        self.method = flag

    def increaseTimePeriod(self):
        for tranche in self._tranches:
            tranche.increaseTimePeriod()

    def resetAllTranches(self):
        for tranche in self._tranches:
            tranche.reset()
        self.reserveAccount = 0
        self.AccuPrincipalCollections = 0

    def makePayments(self, collections, principalCollections):

        availableFunds = collections + self.reserveAccount

        waterfall = []
        for i in range(len(self._tranches)):
            waterfall.append([])

        '''
        make interest payment
        '''
        for i, tranche in enumerate(self._tranches):
            # Case 1: if the balance has been paid up...
            if tranche.pastNotionalBalance.get(tranche.period - 1) <= 10 ** -4:
                interestDue = 0
                interestPaid = 0
                interestShortfall = 0
                waterfall[i].append(interestDue)
                waterfall[i].append(interestPaid)
                waterfall[i].append(interestShortfall)
                tranche.pastInterestPayment[tranche.period] = interestPaid
                tranche.interestShortfall[tranche.period] = interestShortfall
                continue

            # Case 2: if the balance has NOT been paid up...
            interestDue = tranche.interestDue()
            interestPaid = min(interestDue, availableFunds)

            if interestDue > 0:
                tranche.makeInterestPayment(interestPaid)
                availableFunds -= interestPaid
            else:
                tranche.pastInterestPayment[tranche.period] = 0
                tranche.interestShortfall[tranche.period] = 0

            waterfall[i].append(interestDue)
            waterfall[i].append(interestPaid)
            waterfall[i].append(tranche.interestShortfall.get(tranche.period))

        """
        Make principal payment
        """
        sumOfSeniorNotional = 0
        for i, tranche in enumerate(self._tranches):
            # Case 1: if currently there is no fund...
            if availableFunds <= 0:
                principalPaid = 0
                balance = tranche.pastNotionalBalance.get(tranche.period - 1)
                waterfall[i].append(principalPaid)
                waterfall[i].append(balance)

                tranche.pastPrincipalPayment[tranche.period] = principalPaid
                tranche.principalShortfall[tranche.period] = tranche.principalShortfall.get(tranche.period-1)
                tranche.pastNotionalBalance[tranche.period] = balance
                continue
            # Case 2: if the balance has been paid up...
            if tranche.pastNotionalBalance.get(tranche.period - 1) <= 10 ** -4:
                principalPaid = 0
                balance = 0
                waterfall[i].append(principalPaid)
                waterfall[i].append(balance)
                tranche.pastPrincipalPayment[tranche.period] = principalPaid
                tranche.principalShortfall[tranche.period] = 0
                tranche.pastNotionalBalance[tranche.period] = balance
                continue
            # Case 3-1: still need to pay principal due (Sequential)
            if self.method == 'Sequential':

                # pay when senior tranche(s) have all balance paid up by accumulated principal collections
                if self.AccuPrincipalCollections + principalCollections >= sumOfSeniorNotional:
                    principalDue = principalCollections + tranche.principalShortfall.get(tranche.period - 1)
                else:
                    principalDue = 0

                principalPaid = min(principalDue, availableFunds, tranche.pastNotionalBalance.get(tranche.period - 1))
                availableFunds -= principalPaid

                if principalPaid > 0:
                    tranche.makePrincipalPayment(principalPaid, principalDue)
                else:
                    tranche.pastPrincipalPayment[tranche.period] = 0
                    tranche.principalShortfall[tranche.period] = 0

                sumOfSeniorNotional += tranche.notional
                waterfall[i].append(principalPaid)
                waterfall[i].append(tranche.notionalBalance())

            # Case 3-2: still need to pay principal due (ProRata)
            elif self.method == 'ProRata':
                tranche_pct = tranche.notional / self._totalNotional
                principalDue = tranche_pct * principalCollections + tranche.principalShortfall.get(tranche.period - 1)
                principalPaid = min(principalDue, availableFunds, tranche.pastNotionalBalance.get(tranche.period - 1))
                tranche.makePrincipalPayment(principalPaid, principalDue)
                availableFunds -= principalPaid

                waterfall[i].append(principalPaid)
                waterfall[i].append(tranche.notionalBalance())

            # Case 3-3: Error
            else:
                raise ValueError('Invalid principal payment method.')

        self.reserveAccount = availableFunds
        self.AccuPrincipalCollections += principalCollections
        self.waterfalls.append(waterfall)

    def getWaterfall(self, period):
        return self.waterfalls[period-1]












