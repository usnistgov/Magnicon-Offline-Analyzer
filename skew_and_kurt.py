from numpy import sum, sqrt

def skewness(array: list) -> float:
    r1, r2, l = default(array)
    return r2 * (sqrt(l * (l-1))/(l-2))

def kurtosis(array: list) -> float:
    r1, r2, l = default(array)
    return ((((r1-3)*(l+1))+6) * (l-1) * 1/((l-2)*(l-3))) + 3

def default(array: list) -> tuple[float, float, int]:
    l = len(array)
    s = sum(array)
    temp1 = []
    temp2 = []
    temp3 = []
    temp4 = []
    for i, arr in enumerate(array):
        temp1.append(arr - (s/l))
        temp2.append((temp1[i])**2)
        temp3.append(temp2[i]*temp2[i])
        temp4.append(temp1[i]*temp2[i])
    temp1 = sum(temp3)
    temp3 = sum(temp2)/l
    r1    = sum(temp1)/(temp3*temp3*l)
    r2    = sum(temp4)/(temp3*sqrt(temp3)*l)

    return r1, r2, l


if __name__ == '__main__':
    from bvd_stats import bvd_stat
    dat = bvd_stat(r'2023-06-01_CCC\230601_001_1134.txt', T1=25, T2=25, P1=101325, P2=101325)
    print(kurtosis(dat.bvdList))