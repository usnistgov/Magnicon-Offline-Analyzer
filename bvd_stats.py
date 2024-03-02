from magnicon_ccc import magnicon_ccc
from numpy import mean, std, sqrt

# Class that does calculations on the raw data
class bvd_stat:
    def __init__(self, text: str):
        mag = magnicon_ccc(text)
        i      = 0
        points = 0
        start  = False
        cur    = ''
        self.V1      = []
        self.V2      = []
        self.A       = []
        self.stdA    = []
        self.B       = []
        self.stdB    = []
        self.bvdList = []
        temp         = []
        # Runs through the raw data
        while (i < len(mag.rawData)):
            # Ensure the index is not greater than the length of the data
            if i >= len(mag.rawData):
                break
            # Start at the first cycle ramping down
            if mag.phase[i] == 4 and not(start):
                i    += mag.ignored + int((mag.SHC-mag.ignored)/2)
                start = True
                cur   = 'A1'
            # Stores A1 data
            if start and (points != int((mag.SHC-mag.ignored)/2)) and cur == 'A1':
                temp.append(mag.rawData[i])
                points += 1
            # On the last data point calulate the mean and prepare for B1 and B2
            elif start and (points == int((mag.SHC-mag.ignored)/2)) and cur == 'A1':
                # A1 = sum(temp)/len(temp)
                A1     = mean(temp)
                stdA1  = std(temp, ddof=1)
                temp   = []
                points = 0
                cur    = 'B'
                # Ignored samples
                i += mag.ignored
                continue
            if i > len(mag.rawData):
                break
            if start and (points != (mag.SHC-mag.ignored)) and cur == 'B':
                temp.append(mag.rawData[i])
                points += 1
            elif start and (points == (mag.SHC-mag.ignored)) and cur == 'B':
                # B1 = sum(temp[0:int((mag.SHC-mag.ignored)/2)])/len(temp[0:int((mag.SHC-mag.ignored)/2)])
                # B2 = sum(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)])/len(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)])
                B1     = mean(temp[0:int((mag.SHC-mag.ignored)/2)])
                stdB1  = std(temp[0:int((mag.SHC-mag.ignored)/2)], ddof=1)
                B2     = mean(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)])
                stdB2  = std(temp[int((mag.SHC-mag.ignored)/2):(mag.SHC-mag.ignored)], ddof=1)
                temp   = []
                points = 0
                cur    = 'A2'
                i     += mag.ignored
                continue
            if i > len(mag.rawData):
                break
            if start and (points != int((mag.SHC-mag.ignored)/2)) and (cur == 'A2'):
                temp.append(mag.rawData[i])
                points += 1
            # After storing A2, store all the data obtained and prepare to restart back to A1
            elif start and (points == int((mag.SHC-mag.ignored)/2)) and cur == 'A2':
                # A2 = sum(temp)/len(temp)
                A2 = mean(temp)
                stdA2 = std(temp, ddof=1)
                self.V1.append(B2-A1)
                self.V2.append(B1-A2)
                self.A.append(A1)
                self.A.append(A2)
                self.stdA.append(stdA1)
                self.stdA.append(stdA2)
                self.B.append(B1)
                self.B.append(B2)
                self.stdB.append(stdB1)
                self.stdB.append(stdB2)
                temp   = []
                points = 0
                cur    = 'A1'
                continue
            if i > len(mag.rawData):
                break
            i += 1
        for i, V1 in enumerate(self.V1):
            self.bvdList.append((self.V1[i]+self.V2[i])/2)
    
    def send_bvd_stats(self):
        return (self.bvdList, self.V1, self.V2, self.A, self.B, self.stdA, self.stdB)
    
    def clear_bvd_stats(self) -> None:
        self.V1      = []
        self.V2      = []
        self.A       = []
        self.stdA    = []
        self.B       = []
        self.stdB    = []
        self.bvdList = []
        temp         = []
        
        
if __name__ == '__main__':
    print ("I am main")