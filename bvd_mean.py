from magnicon_ccc import magnicon_ccc
# import numpy as np
from numpy import sqrt, mean, std

# Class that does calculations on the raw data
class bvd_mean:
    def __init__(self, text, T1, T2, P1, P2):
        mag = magnicon_ccc(text)
        i = 0
        self.V1 = []
        self.V2 = []
        self.A = []
        self.B = []
        self.bvdList = []
        temp = []
        start = False
        points = 0
        cur = ''
        # Runs through the raw data
        while (i < len(mag.dataV)):
            # Ensures the index is not greater than the length of the data
            if i >= len(mag.dataV):
                break
            # Start at the first cycle ramping down
            if mag.phase[i] == 4 and not(start):
                i += mag.ignored + int((mag.SHC-mag.ignored)/2)
                start = True
                cur = 'A1'
            # Stores A1 data
            if start and (points != int((mag.SHC-mag.ignored)/2)) and cur == 'A1':
                temp.append(mag.dataV[i])
                points += 1
            # On the last data point calulate the mean and prepare for B1 and B2
            elif start and (points == int((mag.SHC-mag.ignored)/2)) and cur == 'A1':
                # A1 = sum(temp)/len(temp)
                A1 = mean(temp)
                temp = []
                points = 0
                cur = 'B'
                # Ignored samples
                i += mag.ignored
                continue
            if i > len(mag.dataV):
                break
            if start and (points != (mag.SHC-mag.ignored)) and cur == 'B':
                temp.append(mag.dataV[i])
                points += 1
            elif start and (points == (mag.SHC-mag.ignored)) and cur == 'B':
                # B1 = sum(temp[0:int((mag.SHC-mag.ignored)/2)])/len(temp[0:int((mag.SHC-mag.ignored)/2)])
                # B2 = sum(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)])/len(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)])
                B1 = mean(temp[0:int((mag.SHC-mag.ignored)/2)])
                B2 = mean(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)])
                temp = []
                points = 0
                cur = 'A2'
                i += mag.ignored
                continue
            if i > len(mag.dataV):
                break
            if start and (points != int((mag.SHC-mag.ignored)/2)) and (cur == 'A2'):
                temp.append(mag.dataV[i])
                points += 1
            # After storing A2, store all the data obtained and prepare to restart back to A1
            elif start and (points == int((mag.SHC-mag.ignored)/2)) and cur == 'A2':
                # A2 = sum(temp)/len(temp)
                A2 = mean(temp)
                self.V1.append(B2-A1)
                self.V2.append(B1-A2)
                self.A.append(A1)
                self.A.append(A2)
                self.B.append(B1)
                self.B.append(B2)
                temp = []
                points = 0
                cur = 'A1'
                continue
            if i > len(mag.dataV):
                break
            i += 1

        self.results(mag, T1, T2, P1, P2)

    # Results from data
    def results(self, mag, T1, T2, P1, P2):
        # Only here for VSCode
        if 1 != 1:
            mag = magnicon_ccc()
        
        self.k = mag.deltaNApN1/mag.NA
        R1corr = (mag.R1alpha*(T1-mag.R1stdTemp) + mag.R1beta*(T1-mag.R1stdTemp)**2) - (mag.R1pcr*(P1-101325))/1000
        R2corr = (mag.R2alpha*(T2-mag.R2stdTemp) + mag.R2beta*(T2-mag.R2stdTemp)**2) - (mag.R2pcr*(P2-101325))/1000
        self.R1PPM = R1corr + mag.R1Pred
        self.R2PPM = R2corr + mag.R2Pred
        self.R1 = (self.R1PPM/1000000 + 1) * mag.R1NomVal
        self.R2 = (self.R2PPM/1000000 + 1) * mag.R2NomVal

        ratioMeanList = []
        self.R1List = []
        self.R2List = []
        ratioMeanC1 = []
        ratioMeanC2 = []
        C1R1List = []
        C1R2List = []
        C2R1List = []
        C2R2List = []
        for i in range(len(self.V1)):
            self.bvdList.append((self.V1[i]+self.V2[i])/2)
            ratioMeanList.append(mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.bvdList[i]/mag.deltaI2R2))
            self.R1List.append((self.R1/ratioMeanList[i] - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
            self.R2List.append((self.R2*ratioMeanList[i] - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
            ratioMeanC1.append(mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.V1[i]/mag.deltaI2R2))
            ratioMeanC2.append(mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.V2[i]/mag.deltaI2R2))
            C1R1List.append((self.R1/ratioMeanC1[i] - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
            C1R2List.append((self.R2*ratioMeanC1[i] - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
            C2R1List.append((self.R1/ratioMeanC2[i] - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
            C2R2List.append((self.R2*ratioMeanC2[i] - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)

        if self.R1List and self.R2List:
            self.meanR1 = mean(self.R1List)
            self.meanR2 = mean(self.R2List)
            self.stdppm = std(ratioMeanList, ddof=1)/mean(ratioMeanList)
            self.stdR1ppm = std(self.R1List, ddof=1)
            self.stdR2ppm = std(self.R2List, ddof=1)
            self.stdMeanPPM = self.stdppm/sqrt(len(self.R1List))
            # Possible problem with R2
            self.C1R1 = mean(C1R1List)
            self.C1R2 = mean(C1R2List)
            self.C2R1 = mean(C2R1List)
            self.C2R2 = mean(C2R2List)
            self.stdC1R1 = std(C1R1List, ddof=1)
            self.stdC1R2 = std(C1R2List, ddof=1)
            self.stdC2R1 = std(C2R1List, ddof=1)
            self.stdC2R2 = std(C2R2List, ddof=1)
        else:
            self.meanR1 = 0
            self.meanR2 = 0
            self.stdppm = 0
            self.stdMeanPPM = 0
            self.C1R1 = 0
            self.C1R2 = 0
            self.C2R1 = 0
            self.C2R2 = 0
            self.stdC1R1 = 0
            self.stdC1R2 = 0
            self.stdC2R1 = 0
            self.stdC2R2 = 0

        if len(self.bvdList):
            self.mean = mean(self.bvdList)
            self.std = std(self.bvdList, ddof=1)
            self.stdMean = self.std/sqrt(len(self.bvdList))
            self.stdMeanR1 = self.stdR1ppm/sqrt(len(self.R1List))
            self.stdMeanR2 = self.stdR2ppm/sqrt(len(self.R2List))
        else:
            self.bvdMean = 0
            self.std = 0
            self.stdMean = 0
            self.stdMeanR1 = 0
            self.stdMeanR2 = 0
        
        self.ratioMean = mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.mean/mag.deltaI2R2)

        ratioMeanChk = mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + mag.bvdMean/mag.deltaI2R2)
        self.R1MeanChk = (self.R1/ratioMeanChk - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr
        self.R2MeanChk = (self.R2*ratioMeanChk - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr

        self.R1CorVal = ((mag.R1Pred/1000000 + 1) * mag.R1NomVal)
        self.R2CorVal = ((mag.R2Pred/1000000 + 1) * mag.R2NomVal)

        print(self.C1R1-self.C2R1, self.C1R2-self.C2R2)
        
        
        
if __name__ == '__main__':
    file1 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_016_1548.txt'
    file2 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2023-06-01_CCC\230601_001_1134.txt'
    file3 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_001_0935.txt'
    test = bvd_mean(file2, 25, 25, 101325, 101325)
    # test = bvd_mean(file2, 25, 25, 103008, 103008)
    # print(test.ratioMean)