from loan.loan_pool import *
from tranche.securities import *
from loan.loan_base import Loan
from utils.monteCarlo import *
import time
import numpy as np


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


    # Instantiate the StructuredSecurities
    ss = StructuredSecurities(lp.totalPrincipal())
    ss.mode('Sequential')  # 'Sequential' or 'ProRata'

    # Add tranches
    percentA = 50
    ss.addTranche('StandardTranche', percentOfNotional=percentA, rate=0.05, subordination='A')
    ss.addTranche('StandardTranche', percentOfNotional=100 - percentA, rate=0.08, subordination='B')

    # Monte Carlo
    s = time.time()
    # !!! Note: nSim should be divisible by nProc !!! nSim is number of simulation per update in yield
    avgALs, avgDIRRs, newARate, newBRate, iterNum = runMonte(lp, ss, nSim=2000, nProc=20, parallel=True, tolerance=0.005)
    e = time.time()
    print(f'Monte Carlo run takes {(e - s) / 60: .2f} minutes, with {iterNum} updates in yields to converge.')

    print(f'Tranche A has IRR {newARate * 100: .2f}%; '
          f' Reduction in Yield {avgDIRRs["A"]: .2f} bps;'
          f' Average Life {avgALs["A"]: .2f} months;'
          f' Letter Rating {rating(avgDIRRs["A"])}.')

    print(f'Tranche B has IRR {newBRate * 100: .2f}%; '
          f' Reduction in Yield {avgDIRRs["B"]: .2f} bps;'
          f' Average Life {avgALs["B"]: .2f} months;'
          f' Letter Rating {rating(avgDIRRs["B"])}.')

    '''
    Result of nSim=2000, nProc=20, parallel=True, tolerance=0.00
    Monte Carlo run takes  56.71 minutes, with 4 updates in yields to converge.
    
    Waterfall takes time mainly due to high number of loans (1500).
    
    Tranche A has IRR  6.61%;  Reduction in Yield  0.00 bps; Average Life  19.49 months; Letter Rating Aaa.
    Tranche B has IRR  6.75%;  Reduction in Yield  0.00 bps; Average Life  49.04 months; Letter Rating Aaa.
    '''


if __name__ == '__main__':
    main()
