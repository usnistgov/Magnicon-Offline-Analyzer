from time import mktime
from datetime import datetime, timedelta
import sys
from numpy import std
sys.path.append(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\Ali\py\ResDatabase')
from ResDataBase import ResData

# Class for parsing CCC files
class magnicon_ccc:
    def __init__(self, text):
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
    def load_raw(self):
        if not self.validFile:
            return
        self.dataV = []
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
                if line.startswith('com rel. humid (%)'):
                    if 'x' in line:
                        self.relHum = line.split('\t')[-1].rstrip(' \n')
                    else:
                        self.relHum = float(line.split(':')[-1].rstrip(' \n'))
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
                    self.dataV.append(float(line.split('\t')[0]))
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
                t1_str = f'{t1[0]}:{t1[1]}'
                t1_obj = datetime.strptime(t1_str, '%H:%M')
                t1_am_pm = t1_obj.strftime('%I:%M %p')
                t2_str = f'{t2[0]}:{t2[1]}'
                t2_obj = datetime.strptime(t2_str, '%H:%M')
                t2_am_pm = t2_obj.strftime('%I:%M %p')
                self.avgDT = (dt1-dt2)/2
                self.DT = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2]) + timedelta(days = self.avgDT.days, seconds = self.avgDT.seconds, microseconds = self.avgDT.microseconds)
                self.timeStamp = mktime(self.DT.timetuple())
            # Returns the start datetime if there is no stop date
            else:
                self.DT = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2])
                self.timeStamp = mktime(self.DT.timetuple())

            self.startDate = f'{d2[1]}/{d2[2]}/{d2[0]} {t2_am_pm}'
            self.endDate = f'{d1[1]}/{d1[2]}/{d1[0]} {t1_am_pm}'

            # This does not average
            # self.timeStamp = mktime(datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2]).timetuple())
                    

    # Parses the bvd.txt file
    def load_bvd(self):
        if not self.validFile:
            return
        with open (self.bvdFile, "r") as file:
            start = False
            self.bvd = []
            for line in file.readlines():
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
    def load_cfg(self):
        if not self.validFile:
            return
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
                if line.startswith('c1_sum'):
                    self.N1 = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('c2_sum'):
                    self.N2 = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('aux_sum'):
                    self.NA = int(line.split('=')[-1].rstrip(' \n'))
                    if self.NA == 0:
                        self.NA = 1
                if line.startswith("co_amplitude 2"):
                    self.appVolt = float(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('ra_steptime 2'):
                    self.rStepTime = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('ra_stepcount 2'):
                    self.rStepCount = int(line.split('=')[-1].rstrip(' \n'))
                if line.startswith('daq_numcycles_stop'):
                    self.numCycStop = int(line.split('=')[-1].rstrip(' \n'))

    # Calculations using the parsed data
    def calculations(self):
        R = ResData(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\vax_data\resistor data\ARMS\Analysis Files')
        self.R1Pred = R.predictedValueUnix(self.R1SN, self.timeStamp)
        self.R2Pred = R.predictedValueUnix(self.R2SN, self.timeStamp)
        R1index = R.getSNindex(self.R1SN)
        R2index = R.getSNindex(self.R2SN)

        # Finds the data on the two resistors in the CCC files from the resistor database
        self.R1alpha = R.alpha[R1index]
        self.R1beta = R.beta[R1index]
        self.R1stdTemp = R.stdTemp[R1index]
        self.R1pcr = R.pcr[R1index]
        self.R2alpha = R.alpha[R2index]
        self.R2beta = R.beta[R2index]
        self.R2stdTemp = R.stdTemp[R2index]
        self.R2pcr = R.pcr[R2index]

        # Time calculations
        if self.validFile:
            self.rampTime = self.rStepTime*self.rStepCount*2/1000000
            self.fullCyc = self.SHC*self.intTime/self.timeBase * 2
            self.delay = (self.ignored/self.SHC)*(self.SHC*self.intTime/self.timeBase - self.rampTime)
            self.measTime = (self.SHC*self.intTime/self.timeBase) - self.rampTime - self.delay

# For testing
if __name__ == '__main__':
    file1 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_016_1548.txt'
    file2 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2023-06-01_CCC\230601_001_1134.txt'
    file3 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_001_0935.txt'
    mc = magnicon_ccc(file2)
    # print(mc.R2Pred)