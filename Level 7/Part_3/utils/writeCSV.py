def writeAssetWaterfallToCSV(assetOutput, filename):
    lines = [','.join(['Period',
                       'LoanPoolPrincipalDue',
                       'LoanPoolInterestDue',
                       'LoanPoolPaymentDue',
                       'LoanPoolBalance'])]
    t = 1
    for line in assetOutput:
        strLine = [str(number) for number in line]
        lines.append(','.join([str(t)] + strLine))
        t += 1

    outputString = '\n'.join(lines)

    with open(filename, 'w') as fp:
        fp.write(outputString)


def writeLiabilityWaterfallToCSV(liabilityOutput, filename, tranchesNameList):
    lines = []
    header = []
    itemNames = ['InterestDue', 'InterestPaid', 'InterestShortfall', 'PrincipalPaid', 'Balance']
    for trancheName in tranchesNameList:
        for colName in itemNames:
            header.append(f'{trancheName} {colName}')

    lines.append(','.join(['Period'] + header))
    t = 1
    for line in liabilityOutput:
        outputLine = [str(t)]
        for trancheSegment in line:
            strTrancheSegment = [str(number) for number in trancheSegment]
            outputLine += strTrancheSegment
        lines.append(','.join(outputLine))
        t += 1

    outputString = '\n'.join(lines)

    with open(filename, 'w') as fp:
        fp.write(outputString)
