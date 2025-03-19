from loan.loan_pool import *
from tranche.securities import *
from utils.writeCSV import *
import time
import numpy as np
from loan.loan_base import Loan


def main():
    # Create a LoanPool that consists of 1500 loans from the csv file.
    filePath = '/Users/jackyen/PycharmProjects/Level 7/Loans.csv'

    #lp = LoanPool([])
    lp = LoanPool(np.array([], dtype=np.dtype(Loan)))

    with open(filePath, 'r') as fp:
        for n, line in enumerate(fp):
            if n == 0:  # skip the header
                continue
            vals = line.split('\n')[0].split(',')
            loanType = vals[1].replace(" ", "")  # remove the inner spaces
            assetName = vals[5]
            assetValue = vals[6]
            principal = vals[2]
            rate = vals[3]
            term = vals[4]
            loan = LoanPool.createLoan(loanType, assetName, assetValue, principal, rate, term)
            if loan:
                lp.loans = np.append(lp.loans, loan)
                #lp.loans.append(loan)

    print(f'Loan pool has WAR {lp.WAR() * 100: .2f}%.')
    print(f'Loan pool has WAM {lp.WAM(): .2f}.')
    print(f'Loan pool currently has {lp.activeLoanCount(t=0)} loans.')
    print(f'Loan pool has a total of {lp.totalPrincipal()/10**6:.2f} millions in notional.')
    print(f'Loan pool has life of {max([loan.term() for loan in lp.loans])} months.')


    # Instantiate the StructuredSecurities
    ss = StructuredSecurities(lp.totalPrincipal())
    ss.mode('Sequential')  # 'Sequential' or 'ProRata'

    # Add tranches
    ss.addTranche('StandardTranche', percentOfNotional=50, rate=0.0661, subordination='A')
    ss.addTranche('StandardTranche', percentOfNotional=50, rate=0.0675, subordination='B')

    # Do waterfall
    s = time.time()
    assetOutput, liabilityOutput, rsv = doWaterfall(lp, ss)
    e = time.time()
    print(f'A waterfall takes {(e - s): .2f} seconds.')

    # Output CSV files
    writeAssetWaterfallToCSV(assetOutput=assetOutput,
                             filename='/Users/jackyen/PycharmProjects/Level 7/Asset.csv')

    writeLiabilityWaterfallToCSV(liabilityOutput=liabilityOutput,
                                 filename='/Users/jackyen/PycharmProjects/Level 7/Liability.csv',
                                 tranchesNameList=['A', 'B'])

    # Reserve account at the end
    print(f'{rsv / 10**6 :.3f} million was left in the reserve account.')


if __name__ == '__main__':
    main()
