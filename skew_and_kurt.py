from numpy import sum, sqrt, NaN

def skewness(array: list) -> float:
    r1, r2, len_ = default(array)
    if len_ - 2 == 0:
        return NaN
    else:
        return r2 * (sqrt(len_ * (len_-1))/(len_-2))

def kurtosis(array: list) -> float:
    r1, r2, len_ = default(array)
    if len_ - 3 == 0:
        return NaN
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