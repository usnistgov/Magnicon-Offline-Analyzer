import logging
logger = logging.getLogger(__name__)
from time import mktime
from datetime import datetime, timedelta
import sys, os, inspect
from numpy import std, floor, nan
import win32file

# Put ResDataBase.py in branch to use on non-NIST computers
from ResDataBase import ResData
# base directory of the project
if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_dir = sys._MEIPASS
    # base_dir = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        running_mode = "Non-interactive (e.g. 'python Magnicon-Offline-Analyzer.py')"
    except NameError:
        base_dir = os.getcwd()
        running_mode = 'Interactive'
# Class for parsing CCC files
class magnicon_ccc:
    def __init__(self, text: str, dbdir: str, site: str) -> None:
        self.dbdir = dbdir
        self.site = site
        self.text = text
        # Reads in file and checks that it is a .txt file
        if '_bvd.txt' in self.text:
            # If the file is a .txt file, it will parse it along with the bvd and cfg files after it
            self.validFile = True
            self.rawFile = self.text.rstrip('_bvd.txt') + '.txt'
            self.bvdFile = self.text
            self.cfgFile = self.text.rstrip('_bvd.txt') + '_cccdrive.cfg'
            # print (self.rawFile, self.bvdFile, self.cfgFile)
            self.load_raw()
            # print("Raw loaded...")
            self.load_bvd()
            # print("BVD loaded...")
            self.load_cfg()
            # print("Config loaded...")
            self.calculations()
            # print("Calculations done...")
        else:
            self.validFile = False

    # Parses the raw data (first .txt file)
    def load_raw(self) -> None:
        if not self.validFile:
            return
        self.comments = ''
        collectData   = False
        self.rawData  = []
        self.phase    = []
        self.error    = []
        try:
            with open (self.rawFile, "r") as file:
                for line in file.readlines():
                    if line.startswith('R1 Info'):
                        self.R1SN = line.split(':')[-1].rstrip(' \n')
                        self.R1SN = self.R1SN.lstrip(' \t')
                    elif line.startswith('R2 Info'):
                        self.R2SN = line.split(':')[-1].rstrip(' \n')
                        self.R2SN = self.R2SN.lstrip(' \t')
                    elif line.startswith('number of samples per half cycle'):
                        self.SHC = int(line.split(':')[-1].rstrip(' \n'))
                    elif line.startswith('ignored first samples'):
                        self.ignored_first = int(line.split(':')[-1].rstrip(' \n'))
                    elif line.startswith('ignored last samples'):
                        self.ignored_last = int(line.split(':')[-1].rstrip(' \n'))
                    elif line.startswith('remarks'):
                        self.comments = line.split(':')[-1].rstrip(' \n')
                        self.comments = self.comments.lstrip(' \t')
                    elif line.startswith('stop date'):
                        if 'x' in line:
                            stopDate = False
                        else:
                            stopDate = True
                            d1 = [int(line.split('-')[0].lstrip('stop date: \t')), int(line.split('-')[1]), int(line.split('-')[2].rstrip(' \n'))]
                    elif line.startswith('start date'):
                        d2 = [int(line.split('-')[0].lstrip('start date: \t')), int(line.split('-')[1]), int(line.split('-')[2].rstrip(' \n'))]
                    elif line.startswith('stop time'):
                        if 'x' in line:
                            stopDate = False
                        else:
                            stopDate = True
                            t1       = [int(line.split('.')[0].lstrip('stop time: \t')), int(line.split('.')[1]), int(line.split('.')[2].rstrip(' \n'))]
                    elif line.startswith('start time'):
                        t2 = [int(line.split('.')[0].lstrip('start time: \t')), int(line.split('.')[1]), int(line.split('.')[2].rstrip(' \n'))]
                    elif collectData:
                        self.rawData.append(float(line.split('\t')[0]))
                        self.phase.append(int(line.split('\t')[1]))
                        self.error.append(int(line.split('\t')[2]))
                    elif line.startswith('data(V)'):
                        collectData = True
                    elif line.startswith('time base (Hz)'):
                        self.timeBase = line.split(':')[-1].rstrip(' \n')
                        self.timeBase = int(self.timeBase.lstrip(' \t'))
                    elif line.startswith('integration time'):
                        self.intTime = line.split(':')[-1].rstrip(' \n')
                        self.intTime = int(self.intTime.lstrip(' \t'))
                self.samplesUsed = self.SHC - self.ignored_first - self.ignored_last
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            pass

        # Averages the datetime start and stop and creates a timestamp of the average
        if stopDate:
            dt1            = datetime(d1[0], d1[1], d1[2], t1[0], t1[1], t1[2])
            dt2            = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2])
            t1_str         = f'{t1[0]}:{t1[1]}:{t1[2]}'
            t1_obj         = datetime.strptime(t1_str, '%H:%M:%S')
            t1_am_pm       = t1_obj.strftime('%I:%M:%S %p')
            t2_str         = f'{t2[0]}:{t2[1]}:{t2[2]}'
            t2_obj         = datetime.strptime(t2_str, '%H:%M:%S')
            t2_am_pm       = t2_obj.strftime('%I:%M:%S %p')
            self.avgDT     = (dt1-dt2)/2.0
            self.DT        = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2]) + timedelta(days = self.avgDT.days, seconds = self.avgDT.seconds, microseconds = self.avgDT.microseconds)
            self.timeStamp = mktime(self.DT.timetuple())
            self.startDate = f'{d2[1]}/{d2[2]}/{d2[0]} {t2_am_pm}'
            self.endDate   = f'{d1[1]}/{d1[2]}/{d1[0]} {t1_am_pm}'
        # Returns the start datetime if there is no stop date
        else:
            self.startDate = 'xx/xx/xx xx:xx:xx'
            self.endDate = 'xx/xx/xx xx:xx:xx'
            self.DT        = datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2])
            self.timeStamp = mktime(self.DT.timetuple())
        # This does not average
        # self.timeStamp = mktime(datetime(d2[0], d2[1], d2[2], t2[0], t2[1], t2[2]).timetuple())
    # Parses the bvd.txt file
    def load_bvd(self) -> None:
        self.relHum = self.comTemp = self.cnTemp = self.nvTemp = self.deltaNApN1 = self.deltaI2R2 = ''
        if not self.validFile:
            return
        try:
            with open (self.bvdFile, "r") as file:
                start    = False
                self.bvd = []
                for line in file.readlines():
                    if line.startswith('com rel. hum'):
                        try:
                            self.relHum = float(line.split(':')[-1].rstrip(' \n'))
                        except ValueError:
                            self.relHum = 'xx.xx'
                            pass
                    elif line.startswith('com temp'):
                        try:
                            self.comTemp = float(line.split(':')[-1].rstrip(' \n'))
                        except ValueError:
                            self.comTemp = 'xx.xx'
                            pass
                    elif line.startswith('cn temp'):
                        try:
                            self.cnTemp = float(line.split(':')[-1].rstrip(' \n'))
                        except ValueError:
                            self.cnTemp = 'xx.xx'
                            pass
                    elif line.startswith('nv temp'):
                        try:
                            self.nvTemp = float(line.split(':')[-1].rstrip(' \n'))
                        except ValueError:
                            self.nvTemp = 'xx.xx'
                            pass
                    elif line.startswith('delta N1/NA'):
                        self.deltaNApN1 = float(line.split(':')[-1].rstrip(' \n')) * 0.001
                    elif line.startswith('delta (I2*R2)'):
                        self.deltaI2R2 = float(line.split(':')[-1].rstrip(' \n'))
                    elif line.startswith('#points'):
                        start = True
                    if start and line.split()[0].isnumeric():
                        self.bvd.append(float(line.split()[1]))
                array = line.split()
                if array[0].isnumeric():
                    self.bvdMean = float(array[2])
                    self.stddrt = float(array[3])
                else:
                    self.bvd = []
                    self.bvdMean = 0
                    self.stddrt = 0
                if len(self.bvd) > 0:
                    self.bvdStd = std(self.bvd, ddof=1)
                else:
                    self.bvdStd = 0
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            pass

    # Parses the .cfg file
    def load_cfg(self) -> None:
        if not self.validFile:
            return
        self.calmode = self.dac12 = self.upper4 = self.lower8 = self.low16 = self.ncor = self.rangeShunt = self.R1NomVal = self.R2NomVal = self.I1 = self.I2 = self.I1Feedin = self.I2Feedin = nan
        feedinIndex = [-97, -94.5, -92.0, -89.5, -87.0, -84.5, -82.0, -79.5, -77.0, -74.5, -72.0, -69.5, -67.0, -64.5, -62.0,
                       -59.5, -57.0, -54.5, -52.0, -49.5, -47.0, -44.5, -42.0, -39.5, -37.0, -34.5, -32.0, -29.5, -27.0]
        rangeShuntList=[512, 64, 8, 1]
        with open (self.cfgFile, "r") as file:
            for line in file.readlines():
                if line.startswith('r1 ='):
                    if ('12906.4' in line) or ('12.9064' in line):
                        self.R1NomVal = 25812.8074593045/2.0
                    elif ('25812.8' in line) or ('25.8128' in line):
                        self.R1NomVal = 25812.8074593045
                    elif ('992.8' in line) or ('9.928' in line):
                        self.R1NomVal = 25812.8074593045/26.0
                    elif ('8604.2' in line) or ('8.6042' in line):
                        self.R1NomVal = 25812.8074593045/3.0
                    elif ('4302.1' in line) or ('4.3021' in line):
                        self.R1NomVal = 25812.8074593045/6.0
                    elif ('109.3' in line) or ('1.093' in line):
                        self.R1NomVal = 25812.8074593045/236.0
                    elif ('218.7' in line) or ('2.817' in line):
                        self.R1NomVal = 25812.8074593045/118.0
                    else:
                        self.R1NomVal = float(line.split('=')[-1].strip())
                elif line.startswith('r2 ='):
                    if ('12906.4' in line) or ('12.9064' in line):
                        self.R2NomVal = 25812.8074593045/2.0
                    elif ('25812.8' in line) or ('25.8128' in line):
                        self.R2NomVal = 25812.8074593045
                    elif ('992.8' in line) or ('9.928' in line):
                        self.R2NomVal = 25812.8074593045/26.0
                    elif ('8604.2' in line) or ('8.6042' in line):
                        self.R2NomVal = 25812.8074593045/3.0
                    elif ('4302.1' in line) or ('4.3021' in line):
                        self.R2NomVal = 25812.8074593045/6.0
                    elif ('109.3' in line) or ('1.093' in line):
                        self.R2NomVal = 25812.8074593045/236.0
                    elif ('218.7' in line) or ('2.817' in line):
                        self.R2NomVal = 25812.8074593045/118.0
                    else:
                        self.R2NomVal = float(line.split('=')[-1].strip())
                elif line.startswith('cs_amplitude 3'):
                    self.I1 = float(line.split(' = ')[-1].strip())
                elif line.startswith('cs_amplitude 4'):
                    self.I2 = float(line.split(' = ')[-1].strip())
                elif line.startswith('cs_feedin 3'):
                    I1FeedinIndex = int(line.split(' = ')[-1].strip())
                    self.I1Feedin = feedinIndex[I1FeedinIndex - 1]
                elif line.startswith('cs_feedin 4'):
                    I2FeedinIndex = int(line.split(' = ')[-1].strip())
                    self.I2Feedin = feedinIndex[I2FeedinIndex - 1]
                elif line.startswith('c1_sum'):
                    self.N1 = int(line.split(' = ')[-1].strip())
                elif line.startswith('c2_sum'):
                    self.N2 = int(line.split(' = ')[-1].strip())
                elif line.startswith('aux_sum'):
                    self.NA = int(line.split(' = ')[-1].strip())
                    if self.NA == 0:
                        self.NA = 1 # override Na to one if someone forgot...
                elif line.startswith("co_extpower 2"):
                    if 'TRUE' in line:
                        self.extpower = 'ON'
                    else:
                        self.extpower = 'OFF'
                elif line.startswith("co_amplitude 2"):
                    self.screenVolt = line.split(' = ')[-1].strip()
                elif line.startswith('ra_steptime 2'):
                    self.rStepTime = int(line.split(' = ')[-1].strip())
                elif line.startswith('ra_stepcount 2'):
                    self.rStepCount = int(line.split(' = ')[-1].strip())
                elif line.startswith('daq_numcycles_stop'):
                    self.numCycStop = int(line.split(' = ')[-1].strip())
                elif line.startswith('cn_short 3'):
                    self.cnOutput = str(line.split(" = ")[-1].strip())
                    if self.cnOutput == 'TRUE':
                        self.cnOutput = False
                    else:
                        self.cnOutput = True
                elif line.startswith('cn_rangeshunt 3'):
                    self.rangeShunt = rangeShuntList[int(line.split('=')[-1].strip())]
                elif line.startswith('cn_ncor 3'):
                    self.ncor = int(line.split(" = ")[-1].strip())
                elif line.startswith('cn_icdac 3'):
                    self.low16 = int(line.split(" = ")[-1].strip())
                elif line.startswith('cn_smrdac 3'): # defines the lower 8 bits of the 12 bit DAC
                    self.lower8 = int(line.split(" = ")[-1].strip())
                elif line.startswith('cn_vhpdac 3'): # defines the upper 4 bits of the 12 bit DAC
                    self.upper4 = int(line.split(" = ")[-1].strip())
                    self.upper4 = self.upper4<<8
                elif line.startswith('cn_calmode 3'): # compensation cal mode (TRUE or FALSE)
                    calmode = str(line.split(" = ")[-1].strip())
                    if calmode == 'TRUE':
                        self.calmode = True
                    else:
                        self.calmode = False
        if self.lower8 is not nan and self.upper4 is not nan:            
            self.dac12 = self.lower8 + self.upper4
                

    def check_shared_drive_exists(self, drive_path):
        try:
            # Open the handle to the network share
            handle = win32file.CreateFile(
                drive_path,
                win32file.GENERIC_READ,
                win32file.FILE_SHARE_READ,
                None,
                win32file.OPEN_EXISTING,
                win32file.FILE_FLAG_BACKUP_SEMANTICS,
                None
            )
            # Close the handle
            win32file.CloseHandle(handle)
            return True
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            # Error occurred, the share doesn't exist or inaccessible
            return False

    def calculations(self) -> None:
        # Calculations using the parsed data
        if self.dbdir != '':
            # use the directory supplied by user...
            R = ResData(self.dbdir)
        # user directory not supplied...
        else:
            # if site is NIST...
            if self.site == 'NIST':
                p = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\vax_data\resistor data\ARMS\Analysis Files'
                if self.check_shared_drive_exists(r'\\elwood.nist.gov\68_PML'):
                    R = ResData(p)
            else:
                # default to the local one supplied with this project
                # print("Using ResDatabase.dat located at: ", base_dir + r'\data')
                R = ResData(base_dir + r'\data')
        # Finds the data on the two resistors in the CCC files from the resistor database
        if self.R1SN in R.ResDict:
            self.R1NomVal  = R.ResDict[self.R1SN]['NomVal']
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
            self.R2NomVal  = R.ResDict[self.R2SN]['NomVal']
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
            if self.deltaI2R2 == '':
                self.deltaI2R2 = 2*self.I1*self.R1NomVal
            self.appVolt       = self.deltaI2R2/2.0
            self.rampTime      = self.rStepTime*self.rStepCount*2/1000000
            self.fullCyc       = self.SHC*self.intTime/self.timeBase*2
            self.measCyc       = self.numCycStop/2.0
            self.delay         = ((self.SHC - self.samplesUsed)/self.SHC)*(self.SHC*self.intTime/self.timeBase - self.rampTime)
            self.meas          = (self.SHC*self.intTime/self.timeBase) - self.rampTime - self.delay
            self.dt            = self.SHC*2/self.fullCyc
            self.measTime      = self.fullCyc*self.measCyc
            self.measTimeStamp = self.sec2ts(self.measTime)
            # print(self.delay, self.meas, self.dt, self.measTime)
        serviceID = {
            0: '51100S',
            # 1: '51132C',
            # 10: '51133C',
            # 100: '51134C',
            # 1000: '51135C',
            # 10000: '51136C',
            # 100000: '51137C',
            # 1000000: '51138C',
            # 10000000: '51139C',
            # 100000000: '51140C',
            # 1000000000: '51141C',
            # 10000000000: '51142C',
            # 100000000000: '51143C',
            # 1000000000000: '51145C',
            # 10000000000000: '51147C'
        }

        # r1_key = int(self.R1NomVal*10000)
        # r2_key = int(self.R2NomVal*10000)

        # if r1_key in serviceID:
        #     self.R1ID = serviceID[r1_key]
        # else:
        #     self.R1ID = serviceID[0]
        # if r2_key in serviceID:
        #     self.R2ID = serviceID[r2_key]
        # else:
        #     self.R2ID = serviceID[0]
        self.R1ID = serviceID[0]
        self.R2ID = serviceID[0]

    def sec2ts(self, sec: float) -> str:
        a  = [3600, 60, 60]
        ts = []
        for i in a:
            cur = floor(sec/i)
            ts.append(cur)
            sec = sec - i*cur
        return f'{"{:02d}".format(int(ts[0]))}:{"{:02d}".format(int(ts[1]))}:{"{:02d}".format(int(ts[2]))}'

# For testing
if __name__ == '__main__':
    print("I am main")