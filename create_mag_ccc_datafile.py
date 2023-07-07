from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc

class writeDataFile():
    def __init__(self, text, dat_obj, bvd_stat_obj, RStatus, R1Temp, R2Temp, pres, I, polarity, system, probe):
        dataFileName = text.replace('.txt', "")
        dataFileName = f'{dataFileName}_MDSS.txt'
        if 1 != 1:
            bvd_stat_obj = bvd_stat()
            dat_obj = magnicon_ccc()

        with open(dataFileName, 'w') as f:
            if RStatus == 'R1':
                pass
            else:
                f.write(f'{dat_obj.R1NomVal}')
            f.write(f'|{dat_obj.startDate}|{dat_obj.endDate}')
            if RStatus == 'R1':
                f.write(f'|{"{:.6E}".format(dat_obj.I2).replace("E-0", "E-")}')
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
                f.write(f'|???')
            else:
                f.write(f'|{dat_obj.R2SN} ({"{:.4f}".format(dat_obj.R2Pred)})')
                f.write(f'|{dat_obj.R1SN}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.meanR2)}')
                f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdR2ppm)}')
                f.write(f'|{"{:.4f}".format(dat_obj.R1Pred)}')
                f.write(f'|???')
                # f.write(f'|1.2906403862E+4')
            f.write(f'|{bvd_obj.N}')
            f.write(f'|{pres}')
            if RStatus == 'R1':
                f.write(f'|{R1Temp}')
                f.write(f'|{R2Temp}')
            else:
                f.write(f'|{R2Temp}')
                f.write(f'|{R1Temp}')
            if RStatus == 'R1':
                f.write(f'|{"{:.4f}".format(bvd_obj.C1R1)}')
                f.write(f'|{"{:.4f}".format(bvd_obj.C2R1)}')
                f.write(f'|{"{:.6f}".format(bvd_obj.C1R1-bvd_obj.C2R1)}')
                f.write(f'|{"{:.4f}".format(bvd_obj.stdC1R1)}')
                f.write(f'|{"{:.4f}".format(bvd_obj.stdC2R1)}')
            else:
                f.write(f'|{"{:.4f}".format(bvd_obj.C1R2)}')
                f.write(f'|{"{:.4f}".format(bvd_obj.C2R2)}')
                f.write(f'|{"{:.6f}".format(bvd_obj.C1R2-bvd_obj.C2R2)}')
                f.write(f'|{"{:.4f}".format(bvd_obj.stdC1R2)}')
                f.write(f'|{"{:.4f}".format(bvd_obj.stdC2R2)}')
            f.write(f'|{dat_obj.SHC}')
            f.write(f'|{dat_obj.samplesUsed}')
            f.write(f'|{"{:.2f}".format(dat_obj.rampTime)}/{"{:.2f}".format(dat_obj.delay)}/{"{:.2f}".format(dat_obj.measTime)}')
            f.write(f'|{"{:.4f}".format(bvd_obj.R2PPM)}')
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
            f.write(f'|{"{:.6E}".format(bvd_obj.mean).replace("E-0", "E-")}')
            f.write(f'|{I} Feedback({polarity})')
            if RStatus == 'R1':
                f.write(f'|{dat_obj.I1Feedin}')
            else:
                f.write(f'|{dat_obj.I2Feedin}')
            f.write(f'|{dat_obj.extpower}')
            f.write(f'|{dat_obj.comRelHum}|{"{:.2f}".format(dat_obj.comTemp)}|{"{:.2f}".format(dat_obj.cnTemp)}|{"{:.2f}".format(dat_obj.nvTemp)}')
            f.write(f'|{system}/{probe}')
            f.write(f'|51100S|Magnicon CCC Process|StandRes')

if __name__ == '__main__':
    file1 = r'2016-02-18_CCC\160218_016_1548.txt'
    file2 = r'2023-06-01_CCC\230601_001_1134.txt'
    file3 = r'2016-02-18_CCC\160218_001_0935.txt'
    file4 = r'2023-05-31_CCC\230531_008_2200.txt'
    dat_obj = magnicon_ccc(file4)
    bvd_obj = bvd_stat(file4, 25, 25, 101325, 101325)
    test_obj = writeDataFile(text='230531_008_2200.txt', dat_obj=dat_obj, bvd_stat_obj=bvd_obj, RStatus='R2', R2Temp='25.0002', R1Temp='-271.5500', pres='101473.813', I='I2', 
                             polarity='NEG', system='CCC2014-01', probe='Magnicon1')