import logging, inspect
from magnicon_ccc import magnicon_ccc
from numpy import mean, std, array_split, sqrt
from threading import Thread
from time import perf_counter

# Class that does calculations on the raw data
class bvd_stat:
    def __init__(self, text: str, ignored_first: int, ignored_last: int, mag, debug_mode: bool):
        # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s:%(message)s')
        self.logger = logging.getLogger(__name__)
        # print ('Debug mode: ', debug_mode)
        self.debug_mode = debug_mode
        if self.debug_mode:
            self.logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.mag = mag
        self.i              = 0
        self.points         = 0
        self.start          = False
        self.cur            = ''
        self.V1             = []
        self.stdV1          = []
        self.V2             = []
        self.stdV2          = []
        self.AA             = []
        self.AA_2D          = []
        self.A1A2           = []
        self.B1B2           = []
        self.BB             = []
        self.A              = []
        self.stdA           = []
        self.B              = []
        self.BB_2D          = []
        self.stdB           = []
        self.bvdList        = []
        self.stdbvdList     = []
        self.temp           = []
        
        self.zero           = []
        self.bottom         = []
        self.top            = []
        self.ramping_up     = []
        self.ramping_down   = []
        
        self.ignored_first = int(ignored_first)
        self.ignored_last = int(ignored_last)
        self.samples_used = self.mag.SHC - (self.ignored_first + self.ignored_last)
        # self.process_thread = Thread(target = self._process_thread, daemon=True)
        self.process_thread = Thread(target = self._process_thread_new, daemon=True)
        self.process_thread.start()
        self.process_thread.join()

    def _process_thread(self,):
        """
        This thread does not account for measurements ignored from the back of the half cycle (ignored_last field)
        and is much slower in execution
        """
        if self.debug_mode:
            self.logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        start_thread = perf_counter()
        # Runs through the raw data
        while (self.i < len(self.mag.rawData)):
            # Ensure the index is not greater than the length of the data
            if self.i >= len(self.mag.rawData):
                break
            # Start at the first cycle ramping down, this is -I cycle
            if self.mag.phase[self.i] == 4 and not(self.start):
                self.i    += self.mag.SHC - self.samples_used + int((self.samples_used)/2)
                self.start = True
                self.cur   = 'A1'
            # Stores A1 data
            if self.start and (self.points != int((self.samples_used)/2)) and self.cur == 'A1':
                self.temp.append(self.mag.rawData[self.i])
                self.AA.append(self.mag.rawData[self.i])
                self.points += 1
            # On the last data point calulate the mean and prepare for B1 and B2
            elif self.start and (self.points == int((self.samples_used)/2)) and self.cur == 'A1':
                # A1 = sum(temp)/len(temp)
                A1     = mean(self.temp)
                stdA1  = std(self.temp, ddof=1)/len(sqrt(self.temp))
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
                self.BB.append(self.mag.rawData[self.i])
                self.points += 1
            elif self.start and (self.points == (self.samples_used)) and self.cur == 'B':
                # B1 = sum(temp[0:int((self.samples_used)/2)])/len(temp[0:int((self.samples_used)/2)])
                # B2 = sum(temp[int((self.samples_used/2):(self.samples_used)])/len(temp[int((self.samples_used)/2):(self.samples_used)])
                B1     = mean(self.temp[0:int((self.samples_used)/2)])
                stdB1  = std(self.temp[0:int((self.samples_used)/2)], ddof=1)/sqrt(len(self.temp[0:int((self.samples_used)/2)]))
                B2     = mean(self.temp[int((self.samples_used)/2):(self.samples_used)])
                stdB2  = std(self.temp[int((self.samples_used)/2):(self.samples_used)], ddof=1)/sqrt(len(self.temp[int((self.samples_used)/2):(self.samples_used)]))
                self.temp   = []
                self.points = 0
                self.cur    = 'A2'
                self.i     += self.mag.SHC - self.samples_used
                continue
            if self.i > len(self.mag.rawData):
                break
            if self.start and (self.points != int((self.samples_used)/2)) and (self.cur == 'A2'):
                self.temp.append(self.mag.rawData[self.i])
                self.AA.append(self.mag.rawData[self.i])
                self.points += 1
            # After storing A2, store all the data obtained and prepare to restart back to A1
            elif self.start and (self.points == int((self.samples_used)/2)) and self.cur == 'A2':
                # A2 = sum(temp)/len(temp)
                A2 = mean(self.temp)
                stdA2 = std(self.temp, ddof=1)/sqrt(len(self.temp))
                self.V1.append(B2-A1) # C1
                self.stdV1.append(sqrt(stdB2**2 + stdA1**2))
                self.V2.append(B1-A2) # C2
                self.stdV2.append(sqrt(stdB1**2 + stdA2**2))
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
        for V1, V2, stdV1, stdV2 in zip(self.V1, self.V2, self.stdV1, self.stdV2):
            self.bvdList.append((V1 + V2)/2.)
            self.stdbvdList.append(sqrt(stdV1**2 + stdV2**2)/2)
        # print('A', self.A)
        # print('B', self.B)
        # print('AA', self.AA)
        # print('BB', self.BB)
        # print('V1', self.V1)
        # print('V2', self.V2)
        # print('BVD', self.bvdList)
        print("Time taken to execute old thread: ", perf_counter() - start_thread)

    def _process_thread_new(self,):
        """
        This thread accounts for measurements ignored from the back of the half cycle (ignored_last field)
        and is much faster in execution
        Returns
        -------
        None.
        """
        self.clear_bvd_stats()
        if self.debug_mode:
            self.logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        start_thread = perf_counter()
        flag = False
        if int(self.ignored_last) == 0:
            ignored_last = -1
        else:
            ignored_last = int(self.mag.SHC) - int(self.ignored_last)
        if int(self.ignored_first) == 0:
            ignored_first = 0
        else:
            ignored_first = self.ignored_first
        # print(len(self.mag.phase), len(self.mag.rawData))
        ct = 0
        for i, j  in zip(self.mag.phase, self.mag.rawData):
            # start at the first cycle ramping down...
            if i != 4 and flag != True:
                ct = ct+1
                # print('Skipping until first rampdown...', ct, i)
                continue
            # seperating all raw data by phases....
            if i == 0:
                self.zero.append(j)
            if i == 0 or i == 1 or i == 3:
                self.top.append(j)
            if i == 0 or i == 2 or i == 4:
                self.bottom.append(j)
            if i == 3:
                self.ramping_up.append(j)
            if i == 4:
                flag = True
                self.ramping_down.append(j)
        self.AA_used = [self.bottom[i * int(self.mag.SHC):(i + 1) * int(self.mag.SHC)] for i in range((len(self.bottom) + int(self.mag.SHC)) // int(self.mag.SHC))] 
        self.BB_used = [self.top[i * int(self.mag.SHC):(i + 1) * int(self.mag.SHC)] for i in range((len(self.top) + int(self.mag.SHC)) // int(self.mag.SHC))]
        for i in self.AA_used:
            # print('AA used length', len(i))
            if len(i) > ((int(self.ignored_first) + int(self.ignored_last))):
                if ignored_last == -1:
                    self.AA_2D.append(i[ignored_first:])
                else:
                    self.AA_2D.append(i[ignored_first:ignored_last])
        for j in self.BB_used:
            if len(j) > ((int(self.ignored_first) + int(self.ignored_last))):
                if ignored_last == -1:
                    self.BB_2D.append(j[ignored_first:])
                else:
                    self.BB_2D.append(j[ignored_first:ignored_last])
        for i in self.AA_2D:
            # print ('AA length', len(i))
            self.A1A2.append(array_split(i, 2))
            self.AA.extend(i)
        for j in self.BB_2D:
            self.B1B2.append(array_split(j, 2))
            self.BB.extend(j)
        for i in self.A1A2:
            for ii in i:
                self.A.append(mean(ii))
                self.stdA.append(std(ii, ddof=1)/sqrt(len(ii)))
        for j in self.B1B2:
            for jj in j:
                self.B.append(mean(jj))
                self.stdB.append(std(jj, ddof=1)/sqrt(len(jj)))
        for a2, b1, stda2, stdb1 in zip(self.A[1::2], self.B[1::2], self.stdA[1::2], self.stdB[1::2]):
            # print (ct, a2, b1)
            self.V1.append(b1 - a2) # C1
            self.stdV1.append(sqrt(stda2**2 + stdb1**2))
        for a1, b2, stda1, stdb2 in zip(self.A[2::2], self.B[0::2], self.stdA[2::2], self.stdB[0::2]):
            # print (ct, a1, b2)
            self.V2.append(b2 - a1) # C2
            self.stdV2.append(sqrt(stda1**2 + stdb2**2))
        for V1, V2, stdV1, stdV2 in zip(self.V1, self.V2, self.stdV1, self.stdV2):
            self.bvdList.append((V1 + V2)/2.)
            self.stdbvdList.append(sqrt(stdV1**2 + stdV2**2)/2)
        # print('A', self.A)
        # print('B', self.B)
        # print('A1A2', self.A1A2)
        # print('B1B2', self.B1B2)
        # print('AA', self.AA)
        # print('BB', self.BB)
        # print('V1', self.V1)
        # print('V2', self.V2)
        # print('BVD', self.bvdList)
        print("Time taken to execute new thread: ", perf_counter() - start_thread)

    def send_bvd_stats(self):
        if self.debug_mode:
            self.logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        return (self.bvdList, self.V1, self.V2, self.A, self.B, self.stdA, self.stdB, self.AA, self.BB, self.stdbvdList)
    
    def clear_bvd_stats(self) -> None:
        if self.debug_mode:
            self.logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.V1             = []
        self.stdV1          = []
        self.V2             = []
        self.stdV2          = []
        self.AA             = []
        self.AA_2D          = []
        self.A1A2           = []
        self.B1B2           = []
        self.BB             = []
        self.A              = []
        self.stdA           = []
        self.B              = []
        self.BB_2D          = []
        self.stdB           = []
        self.bvdList        = []
        self.stdbvdList     = []
        self.temp           = []
        self.zero           = []
        self.bottom         = []
        self.top            = []
        self.ramping_up     = []
        self.ramping_down   = []
        
        
if __name__ == '__main__':
    debug = False
    if debug:
        mag = magnicon_ccc(r'M:\MagniconData\CCCViewerData\cccviewer_measure\2024-05-24_CCC\240524_001_0904_bvd.txt', '')
        bvd_stat_obj = bvd_stat(r'M:\MagniconData\CCCViewerData\cccviewer_measure\2024-05-24_CCC\240524_001_0904_bvd.txt', 16, mag)
        print ("I am main")