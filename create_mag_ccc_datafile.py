from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc

class writeDataFile():
    def __init__(self, text, dat_obj, bvd_stat_obj, RStatus):
        dataFileName = text.replace('.txt', "")
        dataFileName = f'{dataFileName}_MDSS.txt'
        if 1 != 1:
            bvd_stat_obj = bvd_stat()
            dat_obj = magnicon_ccc()

        # R1 vs R2 Standard ??
        with open(dataFileName, 'w') as f:
            f.write(f'{dat_obj.R1NomVal}')
            f.write(f'|{dat_obj.startDate}|{dat_obj.endDate}')
            f.write(f'|{dat_obj.I2}')
            f.write(f'|{"{:.2f}".format(dat_obj.fullCyc)}')
            f.write(f'|{dat_obj.N1}/{dat_obj.N2}')
            f.write(f'|{dat_obj.R2SN} ({"{:.4f}".format(dat_obj.R2Pred)})')
            f.write(f'|{dat_obj.R1SN}')
            f.write(f'|{"{:.4f}".format(bvd_stat_obj.meanR2)}')
            f.write(f'|{"{:.4f}".format(bvd_stat_obj.stdR2ppm)}')
            f.write(f'|{"{:.4f}".format(dat_obj.R1Pred)}')
            if dat_obj.R2NomVal == 100:
                f.write(f'|1.2906403862E+4')
            # elif dat_obj.R2NomVal == 1000:
            #     f.write(f'|{float(1.2906403862E+4)/13}')
            f.write(f'|{bvd_obj.N}')
            f.write(f'|???')
            f.write(f'|???')
            f.write(f'|???')
            if RStatus == 'R1':
                pass
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
            f.write(f'|{"{:.4f}".format(dat_obj.R2pcr)}')
            f.write(f'|{"{:.4f}".format(dat_obj.R2alpha)}')
            f.write(f'|{"{:.4f}".format(dat_obj.R2beta)}')
            f.write(f'|???')
            f.write(f'|???')
            f.write(f'|???')
            f.write(f'|{dat_obj.appVolt}')
            f.write(f'|{"{:.6e}".format(bvd_obj.mean)}')
            f.write(f'|???')
            f.write(f'|???')
            f.write(f'|???')
            # Temps
            f.write(f'|{dat_obj.comRelHum}|{"{:.2f}".format(dat_obj.comTemp)}|{"{:.2f}".format(dat_obj.cnTemp)}|{"{:.2f}".format(dat_obj.nvTemp)}')
            f.write(f'|???')
            f.write(f'|???')
            f.write(f'|???')
            f.write(f'|???')

if __name__ == '__main__':
    file1 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_016_1548.txt'
    file2 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2023-06-01_CCC\230601_001_1134.txt'
    file3 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_001_0935.txt'
    file4 = r'2023-05-31_CCC\230531_008_2200.txt'
    dat_obj = magnicon_ccc(file4)
    bvd_obj = bvd_stat(file4, 25, 25, 101325, 101325)
    test_obj = writeDataFile('230531_008_2200.txt', dat_obj, bvd_obj, 'R2')