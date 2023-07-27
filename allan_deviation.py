from magnicon_ccc import magnicon_ccc
from numpy import sqrt, mean
from math import floor
import os
bp = os.getcwd()

class allan:
    def __init__(self, input_array: list, allan_type: str, overlapping: bool):

        tau = floor(len(input_array)/2)
        
        if allan_type == 'all':
            self.allTau(input_array, tau, overlapping)

        elif allan_type == '2^n':
            self.twoCaretn(input_array, tau, overlapping)

        self.x_fit, self.y_fit = fit_line(self.samples, self.tau_array)

    def allTau(self, input_array: list, tau: int, overlapping: bool):
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
    
    def twoCaretn(self, input_array: list, tau: int, overlapping: bool):
        self.samples = []
        self.tau_array = []
        if overlapping:
            for i in range(tau):
                tau_out = self.overlapping(input_array, 2**(i+1))
                if tau_out:
                    self.samples.append(i+1)
                    self.tau_array.append(sqrt(tau_out))
        else:
            for i in range(tau):
                tau_out = self.non_overlapping(input_array, 2**(i+1))
                if tau_out:
                    self.samples.append(i+1)
                    self.tau_array.append(sqrt(tau_out))

    def non_overlapping(self, input_array: list, tau: int):
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
        if len(temp_array) >= 2:
            temp_array.pop(0)
            return (mean(temp_array)/2)
        else:
            return False
    
    def overlapping(self, input_array: list, tau: int):
        csum = self.cumsum(input_array)
        i = 0
        n = 1
        x = len(input_array)
        y = tau*2 + i
        temp_array = []
        temp1 = LabViewArray(csum, y)
        temp2 = LabViewArray(csum, tau+i)
        temp3 = LabViewArray(csum, i)
        temp_array.append((temp1 - temp2 + temp3)**2)
        while x > y:
            i += 1
            n += 1
            y = tau*2 + i
            temp1 = LabViewArray(csum, y)
            temp2 = LabViewArray(csum, tau+i)
            temp3 = LabViewArray(csum, i)
            temp_array.append((temp1 - temp2 + temp3)**2)
        i += 1
        n += 1
        y = tau*2 + i
        temp1 = LabViewArray(csum, y)
        temp2 = LabViewArray(csum, tau+i)
        temp3 = LabViewArray(csum, i)
        temp_array.append((temp1 - temp2 + temp3)**2)
        return ((sum(temp_array)/n)/(tau*2*tau))
    
    def cumsum(self, input_array: list):
        N = len(input_array)
        cumsum = []
        for i in range(N):
            temp_array = input_array[0:N-i-1]
            cumsum.append(sum(temp_array))
        return cumsum

def LabViewArray(input_array: list, index: int):
    if index < len(input_array):
        return input_array[index]
    else:
        return 0
    
def fit_line(samples: list, tau_array: list):
    end = floor(len(samples)/2)
    m = (tau_array[end]-tau_array[0])/(samples[end]-samples[0])
    c = tau_array[0] - m*samples[0]
    x_fit = []
    y_fit = []
    for i in range(len(samples)):
        # x_fit.append(i+1)
        y_fit.append(m*samples[i] + c)
    return x_fit, y_fit


if __name__ == '__main__':
    file2 = bp + r'\2023-06-01_CCC\230601_001_1134.txt'
    file4 = bp + r'\2023-05-31_CCC\230531_008_2200.txt'
    dat_obj = magnicon_ccc(file2)
    test = allan(input_array=dat_obj.bvd, allan_type='2^n', overlapping=False)
    import mystat
    import matplotlib.pyplot as plt
    print(mystat.AllanDeviation(dat_obj.bvd))
    print(test.tau_array)
    print(test.samples)