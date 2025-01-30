# from scipy.signal import welch
from time import perf_counter
import mystat
import numpy as np
import scipy
from matplotlib import pyplot as plt
import spectral

# globals
SAMPLE_RATE = 100  # Hertz
DURATION = 10  # Seconds

def generate_sine_wave(freq, sample_rate, duration):
    x = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    frequencies = x * freq
    # 2pi because np.sin takes radians
    y = 2*np.sin((2 * np.pi) * frequencies) #+ 2*np.cos(10 * np.pi * frequencies) + 2*np.tan(10 * np.pi * frequencies)
    return x, y

if __name__ == "__main__":
    # Generate a 2 hertz sine wave that lasts for 5 seconds
    x, y = generate_sine_wave(2, SAMPLE_RATE, DURATION)
    welch_start = perf_counter()
    # scipy fft using welch method
    freq2, power2=scipy.signal.welch(np.array(y), fs=SAMPLE_RATE, window='hann', \
                                     nperseg=10*len(y),  scaling='density', \
                                     axis=-1, average='mean', return_onesided=True)
    print('Scipy signal welch time taken: ', perf_counter() - welch_start)
    samp_freq = SAMPLE_RATE
    norm_mystat = []
     # Create the window function
    mystat_start = perf_counter()
    mywindow_mystat = mystat.hann(float(samp_freq), (len(y)*float(samp_freq)))
    norm_mystat.append(mystat.norm_window(mywindow_mystat))
    # Ali's fft
    freq_bvd, mypsa_bvd = mystat.calc_fft((float(samp_freq)), np.array(y), np.array(mywindow_mystat))
    print('My stat FFT time taken: ', perf_counter() - mystat_start)
    # create the window function from stephan's code
    mywindow_spectral = []
    nnorm_spectral = []
    freq_spectral = []
    psd_spectral = []
    # Stefan's fft
    for l in range(len(y)):
        mywindow_spectral.append(spectral.f_hann(l, len(y)))
    norm_spectral = spectral.norm_win(mywindow_spectral)
    # find the normalization factor from stephan's code
    nnorm_spectral.append(norm_spectral)
    mypsa_spectral_tuple = spectral.mypsa(np.array(y), 1./(float(samp_freq)))
    freq_spectral.append(mypsa_spectral_tuple[1])
    psd_spectral.append(mypsa_spectral_tuple[0])
    # print ('PSD Spectral', psd_spectral)
    print (freq2, freq_bvd, freq_spectral)

    fig = plt.figure()
    ax1 = fig.add_subplot(411)
    ax2 = fig.add_subplot(412)
    ax3 = fig.add_subplot(413)
    ax4 = fig.add_subplot(414)

    ax1.plot(x, y)
    ax2.plot(freq2, power2)
    ax3.plot(freq_bvd, mypsa_bvd*np.conj(mypsa_bvd))
    ax4.plot(freq_spectral[0], psd_spectral[0]* np.conj(psd_spectral[0]))

    ax2.set_yscale('log')
    ax2.set_xscale('log')
    ax3.set_yscale('log')
    ax3.set_xscale('log')
    ax4.set_yscale('log')
    ax4.set_xscale('log')
    
    # print(np.max(mypsa_bvd * np.conj(mypsa_bvd) - power2))
    plt.show()