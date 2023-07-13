from magnicon_ccc import magnicon_ccc
import os
import numpy as np

import matplotlib.pyplot as plt

bp = os.getcwd()

class get_fourier:
    def __init__(self, signal, dt):
        N = len(signal)
        han = np.hanning(N)
        fourier = np.fft.fft(han)
        r = []
        Y = []
        for i in range(len(fourier)):
            r.append(abs(fourier[i]))
            Y.append(r[i]*r[i]/(N*N))
        plt.plot(1/np.ones(len(Y), dtype=int), Y)
        plt.show()

if __name__ == '__main__':
    file2 = bp + r'\2023-06-01_CCC\230601_001_1134.txt'
    dat_obj = magnicon_ccc(file2)
    test = get_fourier(dat_obj.rawData, dat_obj.dt)