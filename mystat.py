#!/usr/bin/env python
""" 
A module to the AllanDeviation and other
statistical measures
"""

from __future__ import division # 5/2=2.5 5//2 = 2
from __future__ import print_function # converts print to function

__author__          =   "Stephan Schlamminger & Alireza Panna"
__email__           =   "schlammi@gmail.com"
__status__          =   "Development"
__date__            =   "08/28/11"
__version__         =   "0.1"

from numpy import sqrt, nan, sum, average, mean, std, array, cumsum, ones, \
                  dot, linalg, sort, arange, linspace, float64, abs, median, \
                  ceil, min, max, multiply, fft, flipud
import math 
import scipy
import warnings

def AllanVariance(d,s=None):
    """
    Stephans code to calculate allan variance given data in terms of fractional frequencies
    Only calculates the non overlapped allan variance (default: tau=2^N)
    s, allanvariance, erro_on_allanvariance = AllanVariance(d,s=None)
    """
    x=1
    if s==None:
        """
        tau = 2^N only
        """
        s=[]
        while x<=len(d)/2:
            s.append(x)
            x=x*2
    N=len(d)
    allan=[]    
    allanerr=[]
    corr_allan=[]
    corr_allanerr=[]
    corr_s=[]
    for tau in s:
        ybar=[]
        co=0
        while co+tau < N+1:
            newybar=average(d[co:co+tau])
            ybar.append(newybar)
            co=co+tau
        co=0
        avar=[]
        while co+1<len(ybar):
            avar.append( (ybar[co+1]-ybar[co])*(ybar[co+1]-ybar[co])/2 )           
            co=co+1
        allan.append(mean(avar))
        if len(avar) == 1:
            allanerr.append(0)
        else:
            allanerr.append(std(avar, ddof=1)/math.sqrt(len(avar)))
            
    for i,j,k in zip(allan, allanerr, s):
        if j != 0:
            corr_allan.append(i)
            corr_allanerr.append(j)
            corr_s.append(k)
    #allan=np.array(allan)/np.mean(d)
#    print (np.array(corr_allan))
    return array(corr_s),array(corr_allan),array(corr_allanerr)
  
def AllanDeviation(d,s=None):
    """
    s, allandeviation, erro_on_allandev = AllanDeviation(d,s=None)
    """

    s,va,vaerr = AllanVariance(d,s)
    std = sqrt(va)
    stderr=[]
    for i in range(len(va)):
        x=va[i]
        si=vaerr[i]
        stderr.append(1.0/2.0/sqrt(x)*si)
    return s,array(std),array(stderr)
    
def frequency2phase(freqdata, rate=None):
    """ integrate fractional frequency data and output phase data
    Parameters
    ----------
    freqdata: np.array
        Data array of fractional frequency measurements (nondimensional)
    rate: float
        The sampling rate for phase or frequency, in Hz
    Returns
    -------
    phasedata: np.array
        Time integral of fractional frequency data, i.e. phase (time) data
        in units of seconds.
        For phase in units of radians, see phase2radians()
    """
    if rate==None:
        rate = 1.
        
    dt = 1.0 / float(rate)
    phasedata = cumsum(freqdata) * dt
    return phasedata
    
def avar(d, overlap, s=None):
    x=1
    avar = []
    allanerr = []
    # if s is not defined tau range is 2^N
    if s == None:
        """
        tau = 2^N only
        """
        s = []
        while x <= len(d)/2:
            s.append(x)
            x = x*2       # 1,2,4,8,16....
    # convert to phase data by integrating the frequency data
    pd = frequency2phase(d)
    N=len(pd)
    for tau in s:
        co = 0
        mysum = 0
        n = 0
        if overlap == 1:
            # overlapping
            stride = 1
        elif overlap == 0:
            # non overlapping
            stride = tau
        while(2*tau+co) < N:
            v = pd[co+2*tau] - 2*pd[co+tau] + pd[co]
            mysum = mysum + v*v
            co += stride
            n = n+1
        if n == 0:
            s.pop(len(s)-1)
        if n != 0:
            mysum = (mysum/n)/(2.0*tau**2)
            avar.append(mysum)
            if len(avar) == 1:
                allanerr.append(0)
            else:
                allanerr.append(std(avar, ddof=1)/math.sqrt(len(avar)))
    return array(s), array(avar), array(allanerr)
    
def adev(d, overlap, s):
    s,va,vaerr = avar(d, overlap, s)
    # allan deviation
    std = sqrt(va)
    stderr=[]
    for i in range(len(va)):
        x=va[i]
        si=vaerr[i]
        stderr.append((0.5/math.sqrt(x))*si)
    return s, array(std), array(stderr)

def meanerr(meanvals, errvals):
    """
    mean, err = meanerr(meanvals, errvals)
    Calculates the weighted mean from an input 1d array of meanvals and errvals
    """
    xsum = 0
    errsum = 0
    for x,err in zip(meanvals,errvals):
        xsum = xsum + x / err /err
        errsum = errsum + 1.0/err/err
    mean = xsum /errsum
    err = math.sqrt(1.0/errsum)
    return mean,err

def weightedMean(vals,errs):
    """
    vm,vm_err,chi2 = weightedMean(vals,errs)
    Calculates the weighted mean from an input 1d array vals
    and a second 1d input array erros
    Output: 
        vm = mean value, 
        vm_err = error value
        chi2 = chi2
        Note if chi2> NDF, one can scale the errors by sqrt(chi2/NDF)
    """

    vm  = sum(vals/(errs*errs))/sum(1.0/(errs*errs))
    vm_err = sqrt(1.0/sum(1.0/(errs*errs)))
    chi2 = sum((vals-vm)**2/errs**2)
    return vm,vm_err,chi2

def meanWithCov(vals,cov):
    """
    mm,err,chi2 = meanWithCov(vals,cov)
    Calculates the mean from an input 1d array and the input's covariance
    matrix cov: vals = (1xN) np.array, cov = (NxN) np.array
    Output: 
        mm = mean value taking into account the covariances
        err = error of the mean
        chi2 = chi2
        Note if chi2> NDF, one can scale the errors by sqrt(chi2/NDF)
    
    """

    A = ones((len(vals),1))
    cov_inverse = linalg.inv(cov)
    T= dot(A.T,cov_inverse)/dot(A.T,dot(cov_inverse,A))
    M = dot(T,vals)
    cov_out  = dot(dot(T,cov),T.T)
    chi2 = dot(dot((vals-M).T,cov_inverse),vals-M)
    mm=M[0]
    err=cov_out[0,0]
    return mm,err,chi2

def nonoverlapMA(data):
    """
    s, ma = nonoverlapMA(data)
    For {Y(T), T=1,2,...m}, calculates Y_n(T) = [X((T-1)n+1) + ... + X(nT)]/n
    where {X(t), t=1,2...m} is some random variable
    Output:
        s = list of n's from 0 to n//2
        ma = 2d list of non overlapping moving averages from 0 to n//2
    """
    n = len(data)
    s = list(range(n//2))
    s.pop(0)
    ma = []
    for i in s:
        if i != 0:
            ybar=[]
            co=0
            while co+i<n+1:
                # find the non overlapping averages of the data for n=1,2....len(d)//2
                newybar=average(data[co:co+i])
                ybar.append(newybar)
                co=co+i
            ma.append(ybar)
    return array(s), array(ma)

def normCdf(data):
    temp = []
    norm_cdf = []
    for i,j in enumerate(data):
        temp.append((j-mean(data))/(std(data)*1.414))
    erf_array = scipy.special.erf(array(temp))
    for i in erf_array:
        norm_cdf.append(0.5*(1+i))
    return array(norm_cdf)
  
def edf(data):
    mysort = sort(data)
    edf = arange(len(mysort))/float(len(mysort))
    return array(edf)

def runningAverage(data):
    """
    
    """
    runningAvrg = []
    for i, j in enumerate(data):
        runningAvrg.append(mean(data[0:i+1]))
    return array(runningAvrg)

def autoRegression(data, lag):
    """
    Formats the data to plot AR(p) models
    """
    if lag != 0:
        return(data[lag:], data[0:-lag])
    else:
        return(data[0:], data[0:])

def lagged(data, lag):
    """
    x_lag, x = lagged(data, lag)
    data is a 1d array and lag is an integer
    Returns the random variable Xt at specified lag.
    
    """
    lag = int(lag)
    return array(data[lag:]), array(data[0:(len(data)-lag)])

def noise1D(data):
    """
    POWER LAW NOISE IDENTIFICATION USING THE LAG 1
    AUTOCORRELATION
    W.J. Riley and C.A. Greenhall
    """
    done = False
    d = 0
    p = 0
    dmin = 0
    dmax=3
    noise_type = ''
   
    while not done:
        r = []
        dmean = mean(data, dtype=float64)
        cov  = (std(data, ddof=1))**2
        cov = cov*(len(data) - 1)
        for i, j in zip(data[0:], data[1:]):
            num = ((i-dmean)*(j-dmean))
            r.append(num)
        r1 = sum(r)/cov
        delta = r1/(1+r1)
        if d > dmin and (delta<0.25 or d>=dmax):
            p = int(-2*(delta + d))
            done=True
        else:
            new_data = []
            for i, j in zip(data[0:], data[1:]):
                new_data.append(j-i)
            data = new_data
            d = d+1
    if p == -2:
        noise_type = 'Random Walk FM'
    elif p == -1:
        noise_type = 'Flicker FM'
    elif p == 0:
        noise_type = 'White FM'
    elif p == 1:
        noise_type = 'Flicker PM'
    elif p == 2:
        noise_type = 'White PM'
        
    return (p, noise_type)

def autoCorrelation(data):
    """
    lag, acf, pci, nci, cutoff_lag = autoCorrelation(data)
    Calculates the auto-correlation of a weakly stationary process {Xt: t E T} at lag i:
                p(i)=Cov[Xt, Xt+i]/Cov[Xt, Xt]
    Note: For stationary processes: p(0)=1 and p(-i)=p(i)
    lag, acf, pci and nci's are 1d arrays
    pci, nci are bounds for 95% confidence interval: |p(i)|>1.96*sqrt((1+2*sum(p(k)^2))/n)
    cutoff_lag is the last lag value outside of the confidence band 
    """
    if len(data) < 50:
        warnings.warn("Dataset is to small to generate valid auto-correlation for the process!", Warning)
    lag =           []
    x_arr =         []
    xlag_arr =      []
    cov_array =     []
    acf =           []
    pci =           []
    xlag_minus_xmean = []
    x_minus_xmean =     []
    cutoff_lag_0 =    0
    # Cov[Xt, Xt]=Var[Xt] for t=0 (0 lag)
    cov  = (std(data, ddof=1))**2
    cov = cov*(len(data) - 1)
    # Useful estimates of p(i) can only made if  i<=n/4
    num_lag = int(len(data)/4)
    for i in map(int, linspace(0, num_lag-1, num_lag)):
        xlag, x = lagged(data, i)
        xlag_arr.append(xlag)
        x_arr.append(x)
    for i, j in zip(xlag_arr, x_arr):
        xlag_minus_xmean.append(i-mean(data, dtype=float64))
        x_minus_xmean.append(j-mean(data, dtype=float64))
    for i,j in zip(x_minus_xmean, xlag_minus_xmean):
        cov_array.append(sum(i*j)) 
#    print (cov_array)
    for ct, i in enumerate(cov_array):
        if cov != 0.:
            acf.append(i/cov)
            lag.append(ct)
        else:
            acf.append(i/cov)
            lag.append(ct)
    # 95% confidence band for the auto-correlation of Xt  
    for i in lag[1:]:
        pci.append(1.96*math.sqrt((1+2*sum([a*b for a, b in zip(acf[1:i+1], acf[1:i+1])]))/len(data)))
    # to keep len same
    pci.insert(0,0)
    for i, j, k in zip(lag[1:], acf[1:], pci[1:]):
        if j > k or j < -k:
            cutoff_lag_0 = i
    # print(cutoff_lag_0, num_lag)
    if cutoff_lag_0 > num_lag:
        cutoff_lag = num_lag
    else:
        cutoff_lag = cutoff_lag_0
    return array(lag), array(acf), array(pci), array([-nci for nci in pci]), cutoff_lag

def autocorrVariance(data, acf, cutoff):
    """
    Calculates the autocorrelated variance given the auto-correlation data and the cutoff lag
    """
    n = len(data)
    coeff = 0
    for i in map(int, linspace(1, cutoff, cutoff)):
        coeff += (2*sum((n-i)*acf[i]))/n
    return abs((1 + coeff)*(std(data, ddof=1)**2)/n), (1 + coeff)

def getBins(data):
    """
    Returns the optimal no. of histogram bins according to the Freedman-Diaconis rule
    """
    n = len(data)
    # Calculate inter quartile range
    data = sorted(data)
    if n % 2 == 0:
        iqr = median(data[((n//2) + 1):]) - median(data[0:(n//2)])
    else:
        iqr = median(data[((n//2) + 2):]) - median(data[0:(n//2)])
    bin_width =  (2 * iqr)/(n ** (1./3))
#    print (bin_width, np.median(data[((n//2) + 1):]), np.median(data[0:(n//2)]))
#    print (np.ceil((np.max(data) - np.min(data))/bin_width))
    return ceil((max(data) - min(data))/bin_width)

def removeDrift(y, x=None):
     if x == None:
        for i, j in enumerate(y):
            x.append(i+1)
     linear      =   lambda x, *p: p[0]+p[1]*x
     
     guess = [0, (y[-1]-y[0])/(x[-1]-x[0])]
     no_drift = []
     lfit = []
     residue = []
     try:
        popt, pcov = scipy.optimize.curve_fit(linear,\
        array(x), array(y), guess, \
        maxfev=1000*(len(x)+1))
     except:
        popt, pcov = guess, None

     for i in linear(array(x), *popt):
        lfit.append(i)
     for i, j in zip(y, lfit):
        residue.append(i-j)
     for i, j in zip(y, residue):
        no_drift.append(i-j)
     return no_drift
    
def hann(n, N):
   myhann = []
   for i in arange(0, N, n, dtype=float):
       if n >= 0 and n <= N:
           myhann.append(0.5*(1-math.cos(2*math.pi*i/N)))
       else:
           myhann.append(0)
   return myhann

def norm_window(mywin):
    s=0
    for i in mywin:
        s=s+(i*i)
    return(s)
         
def calc_fft(Fs, data, mywin):
    """
    Returns the amplitude spectrum of the data
    """
    wnorm = norm_window(mywin)
    # signal
    fx = array(data)
    mywin = array(mywin)
    # Length of the signal
    n = len(fx)
    frq = (fft.rfftfreq(n, 1.0/Fs))
    Fk = (fft.rfft(fx*mywin))
    Fk = abs(Fk)
    Fk = multiply(Fk, (1.0/(math.sqrt(Fs*wnorm))))
    Fk[1:] = sqrt(2)*Fk[1:] # multiply by sqrt(2) for single sided psa
    return frq, Fk
    
def psd(Fs, data):
    """
    Returns power spectral density
    """
    frq, Fk = fft(Fs, data)
    return frq, (Fk**2)
    
def crossCorrelation(data1, data2):
    """
    """
    m = len(data1)
    n = len(data2)
    mylag = (arange(-len(data1)//2 + 1,  len(data1)//2 + 1))
    # method 1
    f1 = fft.fft(array(data1))
    # reverse the time series data and take the transform
    f2 = fft.fft(flipud(array(data2)))
    cc = abs((fft.ifft(multiply(array(f1), array(f2)))))
    # method 2    
#    cc1 = np.correlate(np.array(data1) - np.mean(data1), np.array(data2) - np.mean(data2), 'same')
#    ccor = cc1/(np.std(data1)*np.std(data2)*len(data1))
    # method 3
#    cc2 = scipy.signal.fftconvolve(np.array(data1), np.array(data2[::-1]), mode='full')

    return mylag, cc

def skewness(array: list) -> float:
    r1, r2, len_ = default(array)
    if len_ - 2 == 0:
        return nan
    else:
        return r2 * (sqrt(len_ * (len_-1))/(len_-2))

def kurtosis(array: list) -> float:
    r1, r2, len_ = default(array)
    if len_ - 3 == 0:
        return nan
    else:
        return ((((r1-3)*(len_+1))+6) * (len_-1) * 1/((len_-2)*(len_-3))) + 3

def default(array: list) -> tuple[float, float, int]:
    len_  = len(array)
    if len_ == 0:
        r1 = 0
        r2 = 0
    else:
        sum_  = sum(array)
        temp1 = []
        temp2 = []
        temp3 = []
        temp4 = []
        for i, arr in enumerate(array):
            temp1.append(arr - (sum_/len_))
            temp2.append((temp1[i])**2)
            temp3.append(temp2[i]*temp2[i])
            temp4.append(temp1[i]*temp2[i])
        temp1 = sum(temp3)
        temp3 = sum(temp2)/len_
        r1    = sum(temp1)/(temp3*temp3*len_)
        r2    = sum(temp4)/(temp3*sqrt(temp3)*len_)

    return r1, r2, len_

if __name__ == '__main__':
    print ("I am main")