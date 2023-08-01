import numpy as np
import mystat

bvdList = [9.333375000000005e-09, -3.3416250000000073e-09, 3.388124999999994e-09, 
           3.992625000000004e-09, -3.518249999999986e-09, 1.496249999999996e-09, 
           -2.3868750000000165e-09, -2.840624999999982e-09, -2.69925000000001e-09, 
           5.8361250000000036e-09, -1.6301250000000253e-09, -5.0002499999999855e-09, 
           -3.855375000000001e-09, -1.8180000000000233e-09, -6.263624999999999e-09]

norm_hann = []


# def get_spectrum(self):
#     """
#     Returns the single sided amplitude spectrum of the data
#     """
#     self.freq_spectral =    []
#     self.psa_spectral =     []
#     self.freq_mystat =      []
#     self.psa_mystat =       []
#     mywindow_spectral =     []
#     norm_spectral =         []
#     norm_mystat =           []

#     for i, j, k in zip(self.ratio, self.ignore, self.tbp):
#         ####################################################################
#         """
#         Ali's code
#         """
#         # create the window function
# #           mywindow_mystat = mystat.hann(1, len(i) - j)
#         mywindow_mystat = mystat.hann(float(k), (len(i)-j)*float(k))
#         # find the window normalization factor
#         norm_mystat.append(mystat.norm_window(mywindow_mystat))
#         # get the psa
# #            print (len(i[j:]), len(mywindow_mystat))
#         freq_mystat, mypsa_mystat = mystat.fft(1./(float(k)), np.array(i[j:]), np.array(mywindow_mystat))
#         # append the arrays
#         self.freq_mystat.append(freq_mystat)
#         self.psa_mystat.append(mypsa_mystat)