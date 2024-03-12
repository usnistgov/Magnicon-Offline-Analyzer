from magnicon_ccc import magnicon_ccc
from numpy import mean, std, sqrt
from threading import Thread

# Class that does calculations on the raw data
class bvd_stat:
    def __init__(self, text: str, samples_used: int):
        self.mag = magnicon_ccc(text)
        self.i      = 0
        self.points = 0
        self.start  = False
        self.cur    = ''
        self.V1      = []
        self.V2      = []
        self.A       = []
        self.stdA    = []
        self.B       = []
        self.stdB    = []
        self.bvdList = []
        self.temp         = []
        self.samples_used = samples_used
        self.process_thread = Thread(target = self._process_thread, daemon=True)
        self.process_thread.start()
        self.process_thread.join()
        
        # print(self.samples_used)

    
    def _process_thread(self,):
        # Runs through the raw data
        # for a new version this should be in a seperate thread
        while (self.i < len(self.mag.rawData)):
            # Ensure the index is not greater than the length of the data
            if self.i >= len(self.mag.rawData):
                break
            # Start at the first cycle ramping down
            if self.mag.phase[self.i] == 4 and not(self.start):
                self.i    += self.mag.SHC - self.samples_used + int((self.samples_used)/2)
                self.start = True
                self.cur   = 'A1'
            # Stores A1 data
            if self.start and (self.points != int((self.samples_used)/2)) and self.cur == 'A1':
                self.temp.append(self.mag.rawData[self.i])
                self.points += 1
            # On the last data point calulate the mean and prepare for B1 and B2
            elif self.start and (self.points == int((self.samples_used)/2)) and self.cur == 'A1':
                # A1 = sum(temp)/len(temp)
                A1     = mean(self.temp)
                stdA1  = std(self.temp, ddof=1)
                self.temp   = []
                self.points = 0
                self.cur    = 'B'
                # Ignored samples
                self.i += self.mag.SHC - self.samples_used
                continue
            if self.i > len(self.mag.rawData):
                break
            if self.start and (self.points != (self.samples_used)) and self.cur == 'B':
                self.temp.append(self.mag.rawData[self.i])
                self.points += 1
            elif self.start and (self.points == (self.samples_used)) and self.cur == 'B':
                # B1 = sum(temp[0:int((self.samples_used)/2)])/len(temp[0:int((self.samples_used)/2)])
                # B2 = sum(temp[int((self.samples_used/2):(self.samples_used)])/len(temp[int((self.samples_used)/2):(self.samples_used)])
                B1     = mean(self.temp[0:int((self.samples_used)/2)])
                stdB1  = std(self.temp[0:int((self.samples_used)/2)], ddof=1)
                B2     = mean(self.temp[int((self.samples_used)/2):(self.samples_used)])
                stdB2  = std(self.temp[int((self.samples_used)/2):(self.samples_used)], ddof=1)
                self.temp   = []
                self.points = 0
                self.cur    = 'A2'
                self.i     += self.mag.SHC - self.samples_used
                continue
            if self.i > len(self.mag.rawData):
                break
            if self.start and (self.points != int((self.samples_used)/2)) and (self.cur == 'A2'):
                self.temp.append(self.mag.rawData[self.i])
                self.points += 1
            # After storing A2, store all the data obtained and prepare to restart back to A1
            elif self.start and (self.points == int((self.samples_used)/2)) and self.cur == 'A2':
                # A2 = sum(temp)/len(temp)
                A2 = mean(self.temp)
                stdA2 = std(self.temp, ddof=1)
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
                self.temp   = []
                self.points = 0
                self.cur    = 'A1'
                continue
            if self.i > len(self.mag.rawData):
                break
            self.i += 1
        for j, V1 in enumerate(self.V1):
            self.bvdList.append((self.V1[j]+self.V2[j])/2)
        
    
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