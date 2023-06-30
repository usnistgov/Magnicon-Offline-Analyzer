from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc

class writeDataFile():
    def __init__(self, text, dat_obj, bvd_stat_obj, RStatus):
        dataFileName = text.replace('.txt', "")
        dataFileName = f'{dataFileName}_MDSS.txt'
        # bvd_stat_obj = bvd_stat()
        # dat_obj = magnicon_ccc()
        with open(dataFileName, 'w') as f:
            if RStatus == 'R1':
                f.write(f'{dat_obj.R1NomVal}')
                f.write(f'|{dat_obj.startDate}|{dat_obj.endDate}')
                f.write(f'|{dat_obj.I1}')
                f.write(f'|{dat_obj.fullCyc}')
                f.write(f'|{dat_obj.N1}/{dat_obj.N2}')
                f.write(f'|{dat_obj.R2SN} (NEED)')
                f.write(f'|{dat_obj.R1SN}')
                f.write(f'|')
            else:
                f.write(f'{dat_obj.R2NomVal}')
                f.write(f'|{dat_obj.startDate}|{dat_obj.endDate}')
                f.write(f'|{dat_obj.I2}')
                f.write(f'|{dat_obj.fullCyc}')
                f.write(f'|{dat_obj.N1}/{dat_obj.N2}')
                f.write(f'|{dat_obj.R1SN} (NEED)')
                f.write(f'|{dat_obj.R2SN}')
                f.write(f'|')

if __name__ == '__main__':
    file1 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_016_1548.txt'
    file2 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2023-06-01_CCC\230601_001_1134.txt'
    file3 = r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\High Resistance\2023 AJ\Magnicon Gui Files\2016-02-18_CCC\160218_001_0935.txt'
    file4 = r'2023-05-31_CCC\230531_008_2200.txt'
    dat_obj = magnicon_ccc(file4)
    bvd_obj = bvd_stat(file4, 25, 25, 101325, 101325)
    test_obj = writeDataFile('230531_008_2200.txt', dat_obj, bvd_obj, 'R1')