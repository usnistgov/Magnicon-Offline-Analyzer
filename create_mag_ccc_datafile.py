from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
import os

# Class writes the MDSS.txt file
class writeDataFile():
    def __init__(self, savepath: str, text: str, dat_obj: magnicon_ccc, bvd_stat_obj: bvd_stat, \
                 RStatus: str, R1Temp: float, R2Temp: float, R1Pres: float, \
                 R2Pres:float, I: str, polarity: str, system: str, probe: str, \
                 meanR1: float, meanR2: float, stdR1ppm: float, stdR2ppm: float, \
                 R1MeanChkOhm: float, R2MeanChkOhm: float, C1R1: float, C2R1: float, \
                 stdC1R1: float, stdC2R1: float, C1R2: float, C2R2: float, \
                 stdC1R2: float, stdC2R2: float, R1PPM: float, R2PPM: float, \
                 bvd_mean: float, N: int, samplesUsed: int, meas: float, delay: float) -> None:
        # Creates the MDSS file name according to the input .txt file's name
        self.savepath = savepath
        dataFileName = (text.split('/')[-1]).replace('.txt', "")
        dataFileName = self.savepath + os.sep + f'{dataFileName}_MDSS.txt'

        with open(dataFileName, 'w') as f:
            if RStatus == 'R1':
                f.write(f'{dat_obj.R2NomVal}')
            else:
                f.write(f'{dat_obj.R1NomVal}')
            f.write(f'|{dat_obj.startDate}|{dat_obj.endDate}')
            if RStatus == 'R1':
                f.write(f'|{"{:.6E}".format(dat_obj.I1).replace("E-0", "E-")}')
            else:
                f.write(f'|{"{:.6E}".format(dat_obj.I2).replace("E-0", "E-")}')
            f.write(f'|{"{:.2f}".format(dat_obj.fullCyc)}')
            f.write(f'|{dat_obj.N1}/{dat_obj.N2}')
            if RStatus == 'R1':
                f.write(f'|{dat_obj.R1SN} ({"{:.4f}".format(dat_obj.R1Pred)})')
                f.write(f'|{dat_obj.R2SN}')
                f.write(f'|{"{:.4f}".format(meanR1)}')
                f.write(f'|{"{:.4f}".format(stdR1ppm)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2Pred)}')
                f.write(f'|{"{:.10E}".format(R2MeanChkOhm).replace("E+0", "E+")}')
            else:
                f.write(f'|{dat_obj.R2SN} ({"{:.4f}".format(dat_obj.R2Pred)})')
                f.write(f'|{dat_obj.R1SN}')
                f.write(f'|{"{:.4f}".format(meanR2)}')
                f.write(f'|{"{:.4f}".format(stdR2ppm)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1Pred)}')
                f.write(f'|{"{:.10E}".format(R1MeanChkOhm).replace("E+0", "E+")}')
            f.write(f'|{N}')
            if RStatus == 'R1':
                f.write(f'|{"{:.3f}".format(R2Pres)}')
            else:
                f.write(f'|{"{:.3f}".format(R1Pres)}')
            if RStatus == 'R1':
                f.write(f'|{"{:.4f}".format(R1Temp)}')
                f.write(f'|{"{:.4f}".format(R2Temp)}')
            else:
                f.write(f'|{"{:.4f}".format(R2Temp)}')
                f.write(f'|{"{:.4f}".format(R1Temp)}')
            if RStatus == 'R1':
                f.write(f'|{"{:.4f}".format(C1R1)}')
                f.write(f'|{"{:.4f}".format(C2R1)}')
                f.write(f'|{"{:.6f}".format(C1R1-C2R1)}')
                f.write(f'|{"{:.4f}".format(stdC1R1)}')
                f.write(f'|{"{:.4f}".format(stdC2R1)}')
            else:
                f.write(f'|{"{:.4f}".format(C1R2)}')
                f.write(f'|{"{:.4f}".format(C2R2)}')
                f.write(f'|{"{:.6f}".format(C1R2-C2R2)}')
                f.write(f'|{"{:.4f}".format(stdC1R2)}')
                f.write(f'|{"{:.4f}".format(stdC2R2)}')
            f.write(f'|{dat_obj.SHC}')
            f.write(f'|{samplesUsed}')
            f.write(f'|{"{:.2f}".format(dat_obj.rampTime)}/{"{:.2f}".format(delay)}/{"{:.2f}".format(meas)}')
            if RStatus == 'R1':
                f.write(f'|{"{:.4f}".format(R1PPM)}')
            else:
                f.write(f'|{"{:.4f}".format(R2PPM)}')
            f.write(f'|{dat_obj.comments} ')
            if RStatus == 'R1':
                f.write(f'|{"{:.4f}".format(dat_obj.R1pcr)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1alpha)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1beta)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2pcr)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2alpha)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2beta)}')
            else:
                f.write(f'|{"{:.4f}".format(dat_obj.R2pcr)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2alpha)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2beta)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1pcr)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1alpha)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1beta)}')
            if float(dat_obj.screenVolt) >= 0:
                f.write(f'|+{dat_obj.screenVolt}')
            else:
                f.write(f'|-{dat_obj.screenVolt}')
            f.write(f'|{"{:.6E}".format(bvd_mean).replace("E-0", "E-")}')
            f.write(f'|{I} Feedback({polarity})')
            if I == 'I1':
                f.write(f'|{dat_obj.I1Feedin}')
            else:
                f.write(f'|{dat_obj.I2Feedin}')
            f.write(f'|{dat_obj.extpower}')
            f.write(f'|{dat_obj.relHum}|{"{:.2f}".format(dat_obj.comTemp)}|{"{:.2f}".format(dat_obj.cnTemp)}|{"{:.2f}".format(dat_obj.nvTemp)}')
            f.write(f'|{system}/{probe}')
            if RStatus == 'R1':
                f.write(f'|{dat_obj.R2ID}')
            else:
                f.write(f'|{dat_obj.R1ID}')
            f.write('|Magnicon CCC Process|StandRes')

if __name__ == '__main__':
    print("I am main")