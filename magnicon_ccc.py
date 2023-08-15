from time import mktime
from datetime import datetime, timedelta
import sys, os
from numpy import std, floor

bp = os.getcwd()
# if os.path.exists(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\Ali\py\ResDatabase'):
#     sys.path.append(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\Ali\py\ResDatabase')
#     from ResDataBase import ResData
# else:
#     os.chdir('..')
#     os.chdir('ResDatabase')
#     ResDataDir = os.getcwd()
#     os.chdir('..')
#     os.chdir('Magnicon-Offline-Analyzer')
#     sys.path.append(ResDataDir)
#     from ResDataBase import ResData

# Put ResDataBase.py in branch to use on non-NIST computers
from ResDataBase import ResData

# Class for parsing CCC files
class magnicon_ccc:
    def __init__(self, text: str):
        # Reads in file and checks that it is a .txt file
        if '.txt' in text:
            # If the file is a .txt file, it will parse it along with the bvd and cfg files after it
            self.validFile = True
            self.rawFile = text
            self.bvdFile = text.rstrip('.txt') + '_bvd.txt'
            self.cfgFile = text.rstrip('.txt') + '_cccdrive.cfg'
            self.load_raw()
            self.load_bvd()
            self.load_cfg()
            self.calculations()
        else:
            self.validFile = False

    # Parses the raw data (first .txt file)
    def load_raw(self) -> None:
        if not self.validFile:
            return
        self.rawData = []
        self.phase = []
        self.error = []
        self.comments = ''
        collectData = False
        with open (self.rawFile, "r") as file:
            for line in file.readlines():
                if line.startswith('R1 Info'):
                    self.R1SN = line.split(':')[-1].rstrip(' \n')
                    self.R1SN = self.R1SN.lstrip(' \t')
                if line.startswith('R2 Info'):
                    self.R2SN = line.split(':')[-1].rstrip(' \n')
                    self.R2SN = self.R2SN.lstrip(' \t')
                if line.startswith('number of samples per half cycle'):
                    self.SHC = int(line.split(':')[-1].rstrip(' \n'))
                if line.startswith('ignored first samples'):
                    self.ignored = int(line.split(':')[-1].rstrip(' \n'))
                    self.samplesUsed = self.SHC - self.ignored
                if line.startswith('remarks'):
                    self.comments = line.split(':')[-1].rstrip(' \n')
                    self.comments = self.comments.lstrip(' \t')
                if line.startswith('stop date'):
                    if 'x' in line:
                        stopDate = False
                    else:
                        stopDate = True
                        d1 = [int(line.split('-')[0].lstrip('stop date: \t')), int(line.split('-')[1]), int(line.split('-')[2].rstrip(' \n'))]
                if line.startswith('start date'):
                    d2 = [int(line.split('-')[0].lstrip('start date: \t')), int(line.split('-')[1]), int(line.split('-')[2].rstrip(' \n'))]
                if line.startswith('stop time'):
                    if 'x' in line:
                        stopDate = False
                    else:
                        stopDate = True
                        t1 = [int(line.split('.')[0].lstrip('stop time: \t')), int(line.split('.')[1]), int(line.split('.')[2].rstrip(' \n'))]
                if line.startswith('start time'):
                    t2 = [int(line.split('.')[0].lstrip('start time: \t')), int(line.split('.')[1]), int(line.split('.')[2].rstrip(' \n'))]
                if collectData:
                    self.rawData.append(float(line.split('\t')[0]))
                    self.phase.append(int(line.split('\t')[1]))
                    self.error.append(int(line.split('\t')[2]))
                if line.startswith('data(V)'):
                    collectData = True
                if line.startswith('time base (Hz)'):
                    self.timeBase = line.split(':')[-1].rstrip(' \n')
                    self.timeBase = int(self.timeBase.lstrip(' \t'))
                if line.startswith('integration time'):
                    self.intTime = line.split(':')[-1].rstrip(' \n')
                    self.intTime = int(self.intTime.lstrip(' \t'))

        # Averages the datetime start and stop and creates a timestamp of the average
        if stopDate:
            dt1 = datetime(d1[0], d1[1], d1[2], t1[0], t1[1], t1[2])
            dt2 = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2])
            t1_str = f'{t1[0]}:{t1[1]}:{t1[2]}'
            t1_obj = datetime.strptime(t1_str, '%H:%M:%S')
            t1_am_pm = t1_obj.strftime('%I:%M:%S %p')
            t2_str = f'{t2[0]}:{t2[1]}:{t2[2]}'
            t2_obj = datetime.strptime(t2_str, '%H:%M:%S')
            t2_am_pm = t2_obj.strftime('%I:%M:%S %p')
            self.avgDT = (dt1-dt2)/2
            self.DT = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2]) + timedelta(days = self.avgDT.days, seconds = self.avgDT.seconds, microseconds = self.avgDT.microseconds)
            self.timeStamp = mktime(self.DT.timetuple())
            self.startDate = f'{d2[1]}/{d2[2]}/{d2[0]} {t2_am_pm}'
            self.endDate = f'{d1[1]}/{d1[2]}/{d1[0]} {t1_am_pm}'
        # Returns the start datetime if there is no stop date
        else:
            self.DT = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2])
            self.timeStamp = mktime(self.DT.timetuple())

        # This does not average
        # self.timeStamp = mktime(datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2]).timetuple())
                    

    # Parses the bvd.txt file
    def load_bvd(self) -> None:
        if not self.validFile:
            return
        with open (self.bvdFile, "r") as file:
            start = False
            self.bvd = []
            for line in file.readlines():
                if line.startswith('com rel. hum'):
                    try:
                        self.relHum = float(line.split(':')[-1].rstrip(' \n'))
                    except ValueError:
                        self.relHum = 'xx.x'
                if line.startswith('com temp'):
                    try:
                        self.comTemp = float(line.split(':')[-1].rstrip(' \n'))
                    except ValueError:
                        self.comTemp = 'xx.xx'
                if line.startswith('cn temp'):
                    try:
                        self.cnTemp = float(line.split(':')[-1].rstrip(' \n'))
                    except ValueError:
                        self.cnTemp = 'xx.xx'
                if line.startswith('nv temp'):
                    try:
                        self.nvTemp = float(line.split(':')[-1].rstrip(' \n'))
                    except ValueError:
                        self.nvTemp = 'xx.xx'
                if line.startswith('delta N1/NA'):
                    self.deltaNApN1 = float(line.split(':')[-1].rstrip(' \n')) * 0.001
                if line.startswith('delta (I2*R2)'):
                    self.deltaI2R2 = float(line.split(':')[-1].rstrip(' \n'))
                if line.startswith('#points'):
                    start = True
                if start and line.split()[0].isnumeric():
                    self.bvd.append(float(line.split()[1]))
            array = line.split()
            if array[0].isnumeric():
                self.bvdMean = float(array[2])
                self.stddrt = float(array[3])
            else:
                self.bvd = 0
                self.bvdMean = 0
                self.stddrt = 0
            self.bvdStd = std(self.bvd, ddof=1)

    # Parses the .cfg file
    def load_cfg(self) -> None:
        if not self.validFile:
            return
        feedinIndex = [-97, -94.5, -92.0, -89.5, -87.0, -84.5, -82.0, -79.5, -77.0, -74.5, -72.0, -69.5, -67.0, -64.5, -62.0, 
                       -59.5, -57.0, -54.5, -52.0, -49.5, -47.0, -44.5, -42.0, -39.5, -37.0, -34.5, -32.0, -29.5, -27.0]
        with open (self.cfgFile, "r") as file:
            for line in file.readlines():
                if line.startswith('r1 '):
                    if ('12906' in line) or ('12.906' in line):
                        self.R1NomVal = 12906.4037296523
                    else:
                        self.R1NomVal = float(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('r2 '):
                    if ('12906' in line) or ('12.906' in line):
                        self.R2NomVal = 12906.4037296523
                    else:
                        self.R2NomVal = float(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('cs_amplitude 3'):
                    self.I1 = float(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('cs_amplitude 4'):
                    self.I2 = float(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('cs_feedin 3'):
                    I1FeedinIndex = int(line.split('=')[-1].rstrip(' \n'))
                    self.I1Feedin = feedinIndex[I1FeedinIndex - 1]
                if line.startswith('cs_feedin 4'):
                    I2FeedinIndex = int(line.split('=')[-1].rstrip(' \n'))
                    self.I2Feedin = feedinIndex[I2FeedinIndex - 1]
                if line.startswith('c1_sum'):
                    self.N1 = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('c2_sum'):
                    self.N2 = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('aux_sum'):
                    self.NA = int(line.split('=')[-1].rstrip(' \n'))
                    if self.NA == 0:
                        self.NA = 1
                if line.startswith("co_extpower 2"):
                    if 'TRUE' in line:
                        self.extpower = 'ON'
                    else:
                        self.extpower = 'OFF'
                if line.startswith("co_amplitude 2"):
                    self.appVolt = line.split('= ')[-1].rstrip(' \n')
                if line.startswith('ra_steptime 2'):
                    self.rStepTime = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('ra_stepcount 2'):
                    self.rStepCount = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('daq_numcycles_stop'):
                    self.numCycStop = int(line.split('=')[-1].rstrip(' \n'))

    # Calculations using the parsed data
    def calculations(self) -> None:
        # try:
        #     R = ResData(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\vax_data\resistor data\ARMS\Analysis Files')
        # except FileNotFoundError:
        #     R = ResData(ResDataDir)
        R = ResData(bp)

        # Finds the data on the two resistors in the CCC files from the resistor database
        if self.R1SN in R.ResDict:
            self.R1alpha   = R.ResDict[self.R1SN]['Alpha']
            self.R1beta    = R.ResDict[self.R1SN]['Beta']
            self.R1stdTemp = R.ResDict[self.R1SN]['StdTemp']
            self.R1pcr     = R.ResDict[self.R1SN]['PCR']
            self.R1Pred    = R.predictedValueUnix(self.R1SN, self.timeStamp)
        else:
            self.R1alpha   = 0
            self.R1beta    = 0
            self.R1stdTemp = 0
            self.R1pcr     = 0
            self.R1Pred    = 0
        if self.R2SN in R.ResDict:
            self.R2alpha   = R.ResDict[self.R2SN]['Alpha']
            self.R2beta    = R.ResDict[self.R2SN]['Beta']
            self.R2stdTemp = R.ResDict[self.R2SN]['StdTemp']
            self.R2pcr     = R.ResDict[self.R2SN]['PCR']
            self.R2Pred    = R.predictedValueUnix(self.R2SN, self.timeStamp)
        else:
            self.R2alpha   = 0
            self.R2beta    = 0
            self.R2stdTemp = 0
            self.R2pcr     = 0
            self.R2Pred    = 0

        # Time calculations
        if self.validFile:
            self.rampTime = self.rStepTime*self.rStepCount*2/1000000
            self.fullCyc = self.SHC*self.intTime/self.timeBase * 2
            self.measCyc = self.numCycStop/2
            self.delay = (self.ignored/self.SHC)*(self.SHC*self.intTime/self.timeBase - self.rampTime)
            self.meas = (self.SHC*self.intTime/self.timeBase) - self.rampTime - self.delay
            self.dt = self.SHC*2/self.fullCyc
            self.measTime = self.fullCyc*self.measCyc
            self.measTimeStamp = self.sec2ts(self.measTime)

    def sec2ts(self, sec: float) -> str:
        a = [3600, 60, 60]
        ts = []
        for i in a:
            cur = floor(sec/i)
            ts.append(cur)
            sec = sec - i*cur
        return f'{"{:02d}".format(int(ts[0]))}:{"{:02d}".format(int(ts[1]))}:{"{:02d}".format(int(ts[2]))}'


# For testing
if __name__ == '__main__':
    file1 = bp + r'\2016-02-18_CCC\160218_016_1548.txt'
    file2 = bp + r'\2023-06-01_CCC\230601_001_1134.txt'
    file3 = bp + r'\2016-02-18_CCC\160218_001_0935.txt'
    diffFile = bp + r'/2023-05-31_CCC/230531_008_2200.txt'
    # mc = magnicon_ccc(file2)
    mc = magnicon_ccc(diffFile)
    print(mc.R1Pred)