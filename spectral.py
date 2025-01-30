#!/usr/bin/env python
""" A module to compute power spectra,
cross spectral densities, coherence, &
response function

TODO: Need to check if normalization also works if
the function is called

Note: Average the stuff in the functions, csd, psd, ..
PyScripter
ipython


"""
from __future__ import print_function # converts print to function
from __future__ import division # 5/2=2.5 5//2 = 2

__author__          =   "Stephan Schlamminger"
__email__           =   "schlammi@gmail.com"
__status__          =   "Development"
__date__            =   "11/20/11"
__version__         =   "0.1"

import math
import numpy as np


def subtract_drift(data,order): # order=0 only subtract mean, order 1 : mean +lin drift..
    gen_func=[]
    func1=range(len(data))
    for i in range(order+1):
        tmp=[k**i for k in func1]
        if i!=0:
            tmp=tmp-np.mean(tmp)
            tmp=tmp/max(tmp)
        gen_func.append(np.array(tmp))
    A = np.zeros((order+1,order+1))
    b = np.zeros((order+1,1))
    for i in range(order+1):
        for j in range(order+1):
            A[i,j] = sum(gen_func[i]*gen_func[j])
        b[i] = sum(gen_func[i]*data)
    res=np.dot(np.linalg.inv(A),b)
    sub=np.zeros((1,len(data)))
    for i in range(order+1):
        tmp=gen_func[i]*res[i]
        sub=sub+tmp
    ret=data-sub
    return  ret[0]


def f_rect(x,N):
    """
    Calculates the rectangular window for a window of length N at the point x  elem 0..N-1
    """
    h=0.0
    if (x>=0) and (x<=N-1):
        h=1.0
    return h


def f_hann(x,N):
    """
    Calculates the hann window for a window of length N at the point x  elem 0..N-1
    """
    h=0.0
    if (x>=0) and (x<=N-1):
        h=1.0-math.cos(2*math.pi*x/(N-1.0))
    return h

def f_welch(x,N):   #note that if winlen=N, x=0...N-1
    """
    Calculates the welch window for a window of length N at the point x  elem 0..N-1
    """
    h=0.0
    if (x>=0) and (x<=N-1):
        d=(1.0*x-(1.0*(N-1))/2)/((1.0*N+1.0)/2.0)
        h=1.0-d*d
    return h

def f_win(x,N,wtype=2):
    if wtype==0:
         return f_rect(x,N)
    elif wtype==1:
        return f_welch(x,N)
    elif wtype==2:
        return f_hann(x,N)
    else:
        return f_rect(x,N)

def win_hann(winlen):
    x=range(winlen)
    h=[f_hann(i,winlen) for i in x]
    return h

def win_rect(winlen):
    x=np.ones(winlen)
    return list(x)


def win_hanning(winlen):
    x=range(winlen)
    h=[1-math.cos(math.pi*i/max(x))*math.cos(math.pi*i/max(x)) for i in x]
    return h

def calc_win(winlen,type=2):
    if type==2:
        mywindow=win_hann(winlen)
    else:
        mywindow=win_rect(winlen)
    return mywindow

def norm_win(window):
    s=0;
    t=0;
    for i in window:
        s+=i*i
        t+=1
    return 1.0*s/t

def rho_win(L,D,j,wintype=2):
    """
        Calulates the correlation due to overlapping windows. The window is L
        units long (0..L-1) and the windows are displaced by D. j gives the
        corrleation: j=1 calculates the correlation to the neighbouring window.
        j=2 to the next to the neighbour. wintype gives the type of window:
            0 - rect
            1 - welch
            2 - hann
    """
    mysum=0.0
    wss=0.0
    for i in range(L):
        mysum+=f_win(i,L,wintype)*f_win(i-j*D,L,wintype)
        wss+=f_win(i,L,wintype)*f_win(i,L,wintype)
    return mysum*mysum/wss/wss


def psd_rel_var(L,D,K,wintype=2):
    """
        Calculates the variance of the power spectral density relative to the
        value of the psd. L is the length of the window (in datapoins). D is
        the number of data points that the windows are shifted and K is the
        different windows
    """
    if D==0:
        return 1.0/K
    sum=1.0
    rho=1.0
    j=1.0
    while rho!=0:
        rho=rho_win(L,D,j,wintype)
        sum=sum+(2.0*(K-j))/K*rho
        j=j+1.0;
    return (1.0*sum)/K


def get_segment_starts(N,L,D):
    """
        This function returns the startindices for the overlapping segements to
        calculate the PSD. The list looks like [0,ix1,ix2,ix3,..]. The length
        of the original data stream is N. The length of one segment is L and D
        is the overlap. The  segments run from 0..L-1,ix1..ix1+L-1,....,ixK..
        ixK+L-1, with ix1=D,ix2=2*D,ix3=3*D...
        Note this is in python notation data[ix1:ix1+L]
    """
    a=[0]
    ss=0
    if D==0: return a
    while ss+D+L<=N:
        ss=ss+D
        a.append(ss)
    return a



def get_number_of_segments(N,L,D):
    """
       Calculates the number of windows of length L that fit in a data
        of length N. Each window is displaced by units of D. The function
        returns the number of windows K
    """
    if L>N: return 0
    if D>N: return 1
    if D==0: return 1

    K=(N-L)//D
    return K+1


def get_unused_points(N,L,D):
    """
       Calculates the number of points that are not used if a datset of length
       N is sliced in windows of length L that are staggered by D.
    """
    if L>N: return 0
    if D>N: return N-L
    if D==0: return N-L
    K=(N-L)//D
    Nend=K*D+L
    res=N-Nend
    return res


def psd_rel_var_NLD(N,L,D,wintype=2):
    """
    Calculates the variance of the power spectral density relative to the
    value of the psd. N is the length of the data set.
    L is the length of the window (in datapoins). D is
    the number of data points that the windows are shifted
    """
    var=psd_rel_var(L,D,get_number_of_segments(N,L,D),wintype)
    return var


def r2fft(ind1,ind2):
    newind  = ind1+ind2*complex(0,1)
    fft    = np.fft.fft(newind)
    dM=len(fft)
    M=dM/2
    fft1=np.empty(M+1,dtype=complex)
    fft2=np.empty(M+1,dtype=complex)
    fft1[0]=np.real(fft[0])
    fft2[0]=np.imag(fft[0])
    for k in range(1,M+1):
        fft1[k] = (fft[k]+np.conjugate(fft[dM-k]))*0.5
        fft2[k] = (fft[k]-np.conjugate(fft[dM-k]))*0.5*complex(0,-1)
    newtup=(fft1,fft2)
    return newtup


def mypsd(ind1,dt,wintype=2,L=0,D=0):
    """
    Calculates the power spectral density. The input data is in ind1,
    dt is the time interval between two data points. The parameter
    wintype determines, which window is applied. The parameter L is the length
    of a segment. If L=0 there is only one segment with L=len(ind1). D is the
    overlap between segments. If D=0 it will default to D=L//2
    """
    N = len(ind1)
    if L==0: L=N
    if D==0: D=L//2
#    ind1=ind1-np.mean(ind1)
    window = calc_win(L,wintype)
    wss = norm_win(window)
    startix=get_segment_starts(N,L,D)
    cum=[]
    cumc=0;
    for six in startix:
        eix=six+L
        newind1 = np.multiply(ind1[six:eix],window)
        myfft   = np.fft.rfft(newind1)
        myfft   = np.multiply(myfft,dt*math.sqrt(1.0/wss))
        Sxx     = np.power(np.abs(myfft),2)
        Sxx     = Sxx/dt/L
        Gxx     = Sxx
        Gxx[1:]=Gxx[1:]*2  # times 2, since we calculate the one sided psd
        if len(cum)==0:
            cum=Gxx
        else:
            cum=[cum[n]+Gxx[n] for n in range(len(Gxx))]
        cumc+=1
    if cumc>1:
        cum = [cum[n]/cumc for n in range(len(cum))]
    myfreq=[i*1.0/2.0/dt/(len(cum)-1) for i in range(len(cum))]
    newtup=(cum,myfreq)
    return newtup


def mypsa(ind1,dt,wintype=2,L=0,D=0):
    """
    calculates the power spectral amplitude.
    The input data is in ind1,
    dt is the time interval between two data points. The parameter
    wintype determines, which window is applied. The parameter L is the length
    of a segment. If L=0 there is only one segment with L=len(ind1). D is the
    overlap between segments. If D=0 it will default to D=L//2
    Returns psa,f
    """
    psd,f=mypsd(ind1,dt,wintype,L,D)
    psa=np.sqrt(psd)
    newtup=(psa,f)
    return newtup


def mycsd(ind1,ind2,dt,wintype=2,nr_of_segs=1):
    """
    calculates the cross spectral density
    """
    if len(ind1)!=len(ind2):
        print ("sizes don't match")
        exit
    ind1=ind1-np.mean(ind1)
    ind2=ind2-np.mean(ind2)
    N = len(ind1)
    M=N//(nr_of_segs+1)
    dM=2*M
    if nr_of_segs==1:
        dM=N
    cum=[]
    cumc=0;
    window = calc_win(dM,wintype)
    wss = norm_win(window)
    for i in range(nr_of_segs):
        newind1 = np.multiply(ind1[i*M:i*M+dM],window)
        newind2 = np.multiply(ind2[i*M:i*M+dM],window)
        fft1,fft2=r2fft(newind1,newind2)
        fft1   = np.multiply(fft1,dt*math.sqrt(1.0/wss))
        fft2   = np.multiply(fft2,dt*math.sqrt(1.0/wss))
        Sxy    = np.multiply(np.conjugate(fft1),fft2)/dt/dM
        Gxy    = Sxy
        Gxy[1:-1]=Gxy[1:-1]*2  # times 2, since we calculate the one sided psd
        if len(cum)==0:
            cum=Gxy
        else:
            cum=[cum[n]+Gxy[n] for n in range(len(Gxy))]
        cumc+=1
    if cumc>1:
        cum = [cum[n]/cumc for n in range(len(cum))]
    myfreq=[i*1.0/2.0/dt/(len(cum)-1) for i in range(len(cum))]
    newtup=(cum,myfreq)
    return newtup



def mycoherence(ind1,ind2,dt,wintype=2,nr_of_segs=1):
    """
    coherence is given by coh=|Gxy|^2/(Gxx Gyy)
    Note if nr_of_segs=1 than coherence is always one.
    I still have to think about the statement above.
    """
    if len(ind1)!=len(ind2):
        print ("sizes don't match")
        exit
    ind1=ind1-np.mean(ind1)
    ind2=ind2-np.mean(ind2)
    N = len(ind1)
    M=N//(nr_of_segs+1)
    dM=2*M
    if nr_of_segs==1:
        dM=N
    cumGxx=[]
    cumGyy=[]
    cumGxy=[]
    cumc=0;
    window = calc_win(dM,wintype)
    wss = norm_win(window)
    for i in range(nr_of_segs):
        newind1 = np.multiply(ind1[i*M:i*M+dM],window)
        newind2 = np.multiply(ind2[i*M:i*M+dM],window)
        fft1,fft2=r2fft(newind1,newind2)
        fft1   = np.multiply(fft1,dt*math.sqrt(1.0/wss))
        fft2   = np.multiply(fft2,dt*math.sqrt(1.0/wss))

        Sxx     = np.power(np.abs(fft1),2)
        Sxx     = Sxx/dt/dM
        Gxx     = Sxx
        Gxx[1:-1]=Gxx[1:-1]*2.0  # times 2, since we calculate the one sided psd

        Syy     = np.power(np.abs(fft2),2)
        Syy     = Syy/dt/dM
        Gyy     = Syy
        Gyy[1:-1]=Gyy[1:-1]*2.0  # times 2, since we calculate the one sided psd

        Sxy    = np.multiply(np.conjugate(fft1),fft2)/dt/dM
        Gxy    = Sxy
        Gxy[1:-1]=Gxy[1:-1]*2.0  # times 2, since we calculate the one sided psd

        if len(cumGxx)==0:
            cumGxx=Gxx
            cumGyy=Gyy
            cumGxy=Gxy
        else:
            for n in range(len(Gxx)):
                cumGxx[n]=cumGxx[n]+Gxx[n]
                cumGyy[n]=cumGyy[n]+Gyy[n]
                cumGxy[n]=cumGxy[n]+Gxy[n]
        cumc+=1
    if cumc>1:
        cumGxx=cumGxx/cumc
        cumGyy=cumGyy/cumc
        cumGxy=cumGxy/cumc
    #coherence is given by coh=|Gxy|^2/(Gxx Gyy)
    coh=np.divide(np.power(np.abs(cumGxy),2),np.multiply(cumGxx,cumGyy))
    myfreq=[i*1.0/2.0/dt/(len(coh)-1) for i in range(len(coh))]
    newtup=(coh,myfreq)
    return newtup

def myresp(ind1,ind2,dt,wintype=2,nr_of_segs=1):
    """
    response is given by H=Gxy/Gxx
    """
    if len(ind1)!=len(ind2):
        print ("sizes don't match")
        exit
    ind1=ind1-np.mean(ind1)
    ind2=ind2-np.mean(ind2)
    N = len(ind1)
    M=N//(nr_of_segs+1)
    dM=2*M
    if nr_of_segs==1:
        dM=N
    cumGxx=[]
    cumGxy=[]
    cumc=0;
    window = calc_win(dM,wintype)
    wss = norm_win(window)
    for i in range(nr_of_segs):
        newind1 = np.multiply(ind1[i*M:i*M+2*M],window)
        newind2 = np.multiply(ind2[i*M:i*M+2*M],window)
        fft1,fft2=r2fft(newind1,newind2)
        fft1   = np.multiply(fft1,dt*math.sqrt(1.0/wss))
        fft2   = np.multiply(fft2,dt*math.sqrt(1.0/wss))

        Sxx     = np.power(np.abs(fft1),2)
        Sxx     = Sxx/dt/dM
        Gxx     = Sxx
        Gxx[1:-1]=Gxx[1:-1]*2  # times 2, since we calculate the one sided psd

        Sxy    = np.multiply(np.conjugate(fft1),fft2)/dt/dM
        Gxy    = Sxy
        Gxy[1:-1]=Gxy[1:-1]*2  # times 2, since we calculate the one sided psd

        if len(cumGxx)==0:
            cumGxx=Gxx
            cumGxy=Gxy
        else:
            for n in range(len(Gxx)):
                cumGxx[n]=cumGxx[n]+Gxx[n]
                cumGxy[n]=cumGxy[n]+Gxy[n]
        cumc+=1
    if cumc>1:
        cumGxx=cumGxx/cumc
        cumGxy=cumGxy/cumc
    #response is given by H=Gxy/Gxx
    resp=np.divide(cumGxy,cumGxx)
    myfreq=[i*1.0/2.0/dt/(len(resp)-1) for i in range(len(resp))]
    newtup=(resp,myfreq)
    return newtup

def unwrap_phase(pin):
    pout=[]
    pout.append(pin[0])
    cp=0
    o = pin[0]
    tr=np.pi
    for i in pin[1:]:
        i=i+cp
        if i-o>tr:
            cp=cp-2*np.pi
        if i-o<-tr:
            cp=cp+2*np.pi
        o=i
        pout.append(i+cp)
    return pout
            
            
    

if __name__=="__main__":
    print ("Yes, I am main")
    print (math.cos(0))
