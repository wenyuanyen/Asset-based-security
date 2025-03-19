from loan.loan_pool import *
from tranche.securities import *
from tranche.securities import doWaterfall, StructuredSecurities
import copy
import math
import multiprocessing


def doParallel(batchSize, avgAvgALs, avgAvgDIRRs, kth_process, loanPoolOriginal, structuredSecuritiesOriginal):
    avgALs, avgDIRRs = runSimulation(loanPoolOriginal, structuredSecuritiesOriginal, batchSize)
    for tranche in structuredSecuritiesOriginal:
        avgAvgALs[tranche.subordination] += avgALs.get(tranche.subordination)
        avgAvgDIRRs[tranche.subordination] += avgDIRRs.get(tranche.subordination)


def runSimulationParallel(loanPoolOriginal, structuredSecuritiesOriginal, nSim, nProc):
    batchSize = int(nSim / nProc)
    manager = multiprocessing.Manager()
    avgAvgALs = manager.dict()
    avgAvgDIRRs = manager.dict()

    for tranche in structuredSecuritiesOriginal:
        avgAvgALs[tranche.subordination] = 0
        avgAvgDIRRs[tranche.subordination] = 0

    processes = []

    for k in range(nProc):
        p = multiprocessing.Process(target=doParallel, args=(batchSize,
                                                             avgAvgALs, avgAvgDIRRs,
                                                             k,
                                                             loanPoolOriginal, structuredSecuritiesOriginal))
        processes.append(p)
        p.start()

    # Wait for all worker processes to finish
    for p in processes:
        p.join()

    # divided by number of processes to get the average of averages of AL(DIRR)'s
    for tranche in structuredSecuritiesOriginal:
        avgAvgALs[tranche.subordination] /= nProc
        avgAvgDIRRs[tranche.subordination] /= nProc

    return avgAvgALs, avgAvgDIRRs


def runSimulation(loanPoolOriginal, structuredSecuritiesOriginal, nSim):
    avgALs = dict()
    avgDIRRs = dict()

    for tranche in structuredSecuritiesOriginal:
        avgALs[tranche.subordination] = []
        avgDIRRs[tranche.subordination] = []

    for i in range(nSim):
        '''
        use call by value to prevent altering the original passed object
        '''
        loanPool = copy.deepcopy(loanPoolOriginal)
        structuredSecurities = copy.deepcopy(structuredSecuritiesOriginal)

        # do waterfall, keep AL and DIRR only
        _, _, _, ALs, DIRRs = doWaterfall(loanPool, structuredSecurities, message=False)

        # save AL/DIRR from each tranche
        for tranche in structuredSecurities:
            seniority = tranche.subordination
            if ALs[seniority] != 'Inf':  # exclude infinite AL from average
                avgALs[seniority].append(ALs.get(seniority))
            avgDIRRs[seniority].append(DIRRs.get(seniority))

        # finally, take average
        if i == (nSim - 1):
            for tranche in structuredSecurities:
                seniority = tranche.subordination

                if avgALs[seniority]:
                    avgALs[seniority] = sum(avgALs[seniority]) / len(avgALs[seniority])
                else:  # empty list indicates all AL's have been excluded. Hence, all AL's are Inf
                    raise Exception(f'There exists a waterfall run where every WAL is infinite for a tranche. '
                                    f'Please try a lower initial rate for tranche {seniority}.')

                avgDIRRs[seniority] = sum(avgDIRRs[seniority]) / len(avgDIRRs[seniority])

    return avgALs, avgDIRRs


# (a,d) = (avg AL in months, avg DIRR in basis point)
def calculateYield(a, d):
    return (7 / (1 + 0.08 * math.exp(-0.19 * (a / 12))) + 0.019 * math.sqrt((a / 12) * d * 100)) / 100


def runMonte(loanPoolOriginal, structuredSecuritiesOriginal, nSim, nProc, parallel=True, tolerance=0.0005):
    # initial loan pool & structured security, pass by value
    loanPool = copy.deepcopy(loanPoolOriginal)
    structuredSecurities = copy.deepcopy(structuredSecuritiesOriginal)

    # get rate & notional from the initial loan pool & structured security
    trancheA = getattr(structuredSecuritiesOriginal, '_tranches')[0]
    trancheB = getattr(structuredSecuritiesOriginal, '_tranches')[1]

    lastARate = trancheA.rate
    lastBRate = trancheB.rate
    nA = trancheA.notional
    nB = trancheB.notional

    iterNum = 0

    while True:
        # simulate based on the current loan pool & structured security
        # after the simulation, passed-in loanPool and structuredSecurities do not change
        if parallel:
            avgALs, avgDIRRs = runSimulationParallel(loanPool, structuredSecurities, nSim, nProc)
        else:
            avgALs, avgDIRRs = runSimulation(loanPool, structuredSecurities, nSim)
        iterNum += 1

        # update yield from average AL and DIRR
        for seniority, _ in avgALs.items():
            trancheYield = calculateYield(avgALs.get(seniority), avgDIRRs.get(seniority))
            if seniority == 'A':
                newARate = lastARate + 1.2 * (trancheYield - lastARate)
            if seniority == 'B':
                newBRate = lastBRate + 0.8 * (trancheYield - lastBRate)

        # check the stopping criterion
        diff = (nA * abs((lastARate - newARate) / lastARate) + nB * abs((lastBRate - newBRate) / lastBRate)) / (nA + nB)
        if diff < tolerance:
            break

        # update the tranche rates within structuredSecurities
        for tranche in structuredSecurities:
            seniority = tranche.subordination
            if seniority == 'A':
                tranche.rate = newARate
            if seniority == 'B':
                tranche.rate = newBRate

        # remember the previous tranche rate, for checking the convergence
        lastARate = newARate
        lastBRate = newBRate

    return avgALs, avgDIRRs, newARate, newBRate, iterNum
