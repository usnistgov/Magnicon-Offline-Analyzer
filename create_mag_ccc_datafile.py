from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
import os

bp = os.getcwd()

# Class writes the MDSS.txt file
class writeDataFile():
    def __init__(self, text: str, dat_obj: magnicon_ccc, bvd_stat_obj: bvd_stat, RStatus: str, R1Temp: float, R2Temp: float, R1Pres: float,
                R2Pres:float, I: str, polarity: str, system: str, probe: str) -> None:
        # Creates the MDSS file name according to the input .txt file's name
        dataFileName = text.replace('.txt', "")
        dataFileName = f'{dataFileName}_MDSS.txt'
        
        # Writes the data to the MDSS file
        os.chdir(bp + r'\MDSS Folder')
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
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.meanR1)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdR1ppm)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R2Pred)}')
                f.write(f'|{"{:.10E}".format(bvd_stat_obj.R2MeanChkOhm).replace("E+0", "E+")}')
            else:
                f.write(f'|{dat_obj.R2SN} ({"{:.4f}".format(dat_obj.R2Pred)})')
                f.write(f'|{dat_obj.R1SN}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.meanR2)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdR2ppm)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1Pred)}')
                f.write(f'|{"{:.10E}".format(bvd_stat_obj.R1MeanChkOhm).replace("E+0", "E+")}')
            f.write(f'|{bvd_stat_obj.N}')
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
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.C1R1)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.C2R1)}')
                f.write(f'|{"{:.6f}".format(bvd_stat_obj.C1R1-bvd_stat_obj.C2R1)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdC1R1)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdC2R1)}')
            else:
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.C1R2)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.C2R2)}')
                f.write(f'|{"{:.6f}".format(bvd_stat_obj.C1R2-bvd_stat_obj.C2R2)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdC1R2)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdC2R2)}')
            f.write(f'|{dat_obj.SHC}')
            f.write(f'|{dat_obj.samplesUsed}')
            f.write(f'|{"{:.2f}".format(dat_obj.rampTime)}/{"{:.2f}".format(dat_obj.delay)}/{"{:.2f}".format(dat_obj.measTime)}')
            if RStatus == 'R1':
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.R1PPM)}')
            else:
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.R2PPM)}')
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
            if float(dat_obj.appVolt) >= 0:
                f.write(f'|+{dat_obj.appVolt}')
            else:
                f.write(f'|-{dat_obj.appVolt}')
            f.write(f'|{"{:.6E}".format(bvd_stat_obj.mean).replace("E-0", "E-")}')
            f.write(f'|{I} Feedback({polarity})')
            if I == 'I1':
                f.write(f'|{dat_obj.I1Feedin}')
            else:
                f.write(f'|{dat_obj.I2Feedin}')
            f.write(f'|{dat_obj.extpower}')
            f.write(f'|{dat_obj.relHum}|{"{:.2f}".format(dat_obj.comTemp)}|{"{:.2f}".format(dat_obj.cnTemp)}|{"{:.2f}".format(dat_obj.nvTemp)}')
            f.write(f'|{system}/{probe}')
            f.write(f'|51100S|Magnicon CCC Process|StandRes')

if __name__ == '__main__':
    file1 = bp + r'\2016-02-18_CCC\160218_016_1548.txt'
    file2 = bp + r'\2023-06-01_CCC\230601_001_1134.txt'
    file3 = bp + r'\2016-02-18_CCC\160218_001_0935.txt'
    file4 = bp + r'\2023-05-31_CCC\230531_008_2200.txt'
    dat_obj = magnicon_ccc(file4)
    bvd_stat_obj = bvd_stat(file4, 25, 25, 101325, 101325)
    writeDataFile(text='230531_008_2200.txt', dat_obj=dat_obj, bvd_stat_obj=bvd_stat_obj, RStatus='R2', R2Temp=25.0002, 
                  R1Temp=-271.5500, R1Pres=101473.813, R2Pres=101473.813, I='I2', polarity='NEG', system='CCC2014-01', probe='Magnicon1')