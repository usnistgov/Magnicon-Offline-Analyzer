from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
from numpy import sqrt, mean
from math import floor
import os
bp = os.getcwd()

import matplotlib.pyplot as plt

class allan:
    def __init__(self, input_array, allan_type, overlapping):

        tau = floor(len(input_array)/2)
        
        if allan_type == 'all':
            self.allTau(input_array, tau, overlapping)

        elif allan_type == '2^n':
            self.twoCaretn(input_array, tau, overlapping)

    def allTau(self, input_array, tau, overlapping):
        self.samples = []
        self.tau_array = []
        if overlapping:
            for i in range(tau):
                self.samples.append(i+1)
                tau_out = self.overlapping(input_array, i+1)
                self.tau_array.append(sqrt(tau_out))
        else:
            for i in range(tau):
                self.samples.append(i+1)
                tau_out = self.non_overlapping(input_array, i+1)
                self.tau_array.append(sqrt(tau_out))
        # plt.figure(1)
        # plt.plot(self.samples, tau_array)
        # plt.show()
    
    def twoCaretn(self, input_array, tau, overlapping):
        self.samples = []
        self.tau_array = []
        if overlapping:
            for i in range(tau):
                tau_out = self.non_overlapping(input_array, 2**(i+1))
                if tau_out:
                    self.samples.append(i+1)
                    self.tau_array.append(sqrt(tau_out))
        else:
            for i in range(tau):
                tau_out = self.non_overlapping(input_array, 2**(i+1))
                if tau_out:
                    self.samples.append(i+1)
                    self.tau_array.append(sqrt(tau_out))

    def non_overlapping(self, input_array, tau):
        N = floor(len(input_array)/tau)
        prev_array = input_array
        prev_mean = 0
        temp_array = []
        for i in range(N):
            subarray = prev_array[0:tau]
            prev_array = prev_array[tau:len(prev_array)]
            cur_mean = mean(subarray)
            temp = cur_mean - prev_mean
            prev_mean = cur_mean
            temp_array.append(temp*temp)
        if len(temp_array) > 2:
            temp_array.pop(0)
            return (mean(temp_array)/2)
        else:
            return False
    
    def overlapping(self, input_array, tau):
        i = 0
        csum = self.cumsum(input_array)
        x = len(input_array)
        y = tau*2 + i
        temp_array = []
        temp_array.append((csum[y] - csum[tau+i] + csum[i])**2)
        i = 1
        n = 1
        while x < y:
            temp_array.append((csum[y] - csum[tau+i] + csum[i])**2)
            i += 1
            n += 1
        print((sum(temp_array)/n)/(tau*2*tau))
        return ((sum(temp_array)/n)/(tau*2*tau))
    
    def cumsum(self, input_array):
        N = len(input_array)
        cumsum = []
        for i in range(N):
            temp_array = input_array[0:N-i-1]
            cumsum.append(sum(temp_array))
        return cumsum
    

if __name__ == '__main__':
    file2 = bp + r'\2023-06-01_CCC\230601_001_1134.txt'
    file4 = bp + r'\2023-05-31_CCC\230531_008_2200.txt'
    dat_obj = magnicon_ccc(file2)
    # bvd_stat_obj = bvd_stat(file2, 25, 25, 101325, 101325)

    test = allan(input_array=dat_obj.bvd, allan_type='all', overlapping=True)