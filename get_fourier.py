import numpy as np
import mystat
from magnicon_ccc import magnicon_ccc
import os
import matplotlib.pyplot as plt

bp = os.getcwd()
file = bp + r'\2023-06-01_CCC\230601_001_1134.txt'

def main():
    mag = magnicon_ccc(file)
    
    data = np.array(mag.rawData)
    ps = np.abs(np.fft.fft(data))**2

    dt = 1
    freqs = np.fft.fftfreq(data.size, dt)
    idx = np.argsort(freqs)

    plt.plot(freqs[idx], ps[idx])
    plt.show()
    
    # tbp    = []
    # ignore = []

    # for i in mag.rawData:
    #     tbp.append(mag.meas+mag.delay)
    #     ignore.append(0)

    # a1, a2 = get_spectrum(mag.rawData, ignore, tbp)

def get_spectrum(ratio, ignore, tbp):
    """
    Returns the single sided amplitude spectrum of the data
    """
    freq_mystat = []
    norm_mystat = []
    psa_mystat  = []

    for i, j, k in zip(ratio, ignore, tbp):
        ####################################################################
        """
        Ali's code
        """
        # create the window function
#           mywindow_mystat = mystat.hann(1, len(i) - j)
        mywindow_mystat = mystat.hann(float(k), (len(i)-j)*float(k))
        # find the window normalization factor
        norm_mystat.append(mystat.norm_window(mywindow_mystat))
        # get the psa
#            print (len(i[j:]), len(mywindow_mystat))
        myfreq_mystat, mypsa_mystat = mystat.fft(1./(float(k)), np.array(i[j:]), np.array(mywindow_mystat))
        # append the arrays
        freq_mystat.append(myfreq_mystat)
        psa_mystat.append(mypsa_mystat)
    return freq_mystat, psa_mystat

if __name__ == '__main__':
    main()