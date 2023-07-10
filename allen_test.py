import allantools
from bvd_stats import bvd_stat
from numpy import sqrt, mean, std
import os
bp = os.getcwd()

if __name__ == '__main__':
    f = bp + r'/2023-05-31_CCC/230531_008_2200.txt'
    myObj = bvd_stat(text=f, T1=25, T2=24, P1=101325, P2=101325)
    print(allantools.adev(myObj.bvdList))