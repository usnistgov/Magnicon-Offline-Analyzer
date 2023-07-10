import allantools
from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
from numpy import sqrt, mean, std
import os
bp = os.getcwd()

if __name__ == '__main__':
    f = bp + r'/2023-05-31_CCC/230531_008_2200.txt'
    f1 = bp + r'\2016-02-18_CCC\160218_001_0935.txt'
    myObj = bvd_stat(text=f, T1=25, T2=24, P1=101325, P2=101325)
    print(allantools.adev(myObj.bvdList))