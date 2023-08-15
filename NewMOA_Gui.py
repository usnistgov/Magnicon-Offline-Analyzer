from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from magnicon_ccc import magnicon_ccc
from create_mag_ccc_datafile import writeDataFile
import sys, os

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

from bvd_stats import bvd_stat
from skew_and_kurt import skewness, kurtosis
import tkinter
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter, NullFormatter
from allan_deviation import allan
import numpy as np

# Cleaner code with layout instead of absolute
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle('Magnicon Offline Analyzer')
        self.setWindowIcon(QIcon('analyzer.ico'))
        # self.setGeometry(QRect(0, 0, 961, 791))
        # self.centerOnScreen()
        

    def initUI(self):
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        self.tab1 = self.tab1UI(self.tab1)
        self.tab2 = self.tab2UI(self.tab2)
        self.tab3 = self.tab3UI(self.tab3)

        self.tabs.addTab(self.tab1, 'Settings/Results')
        self.tabs.addTab(self.tab2, 'BVD')        
        self.tabs.addTab(self.tab3, 'Allan Dev.')

        self.setCentralWidget(self.tabs)

    def tab1UI(self, tab1):
        tab1.grid = QGridLayout(tab1)
        tab1.grid.setSpacing(10)
        self.tab1_edits(tab1)

        HSpacer = QSpacerItem(30, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        for i in range(25):
            if i % 2 == 0:
                tab1.grid.addItem(HSpacer, i+1, 2)
            # tab1.grid.addItem(HSpacer, i+1, 4)

        tab1.grid.addWidget(QLabel('Settings'), 1, 4)
        tab1.grid.addWidget(QLabel('R1 Serial Number'), 2, 1)
        tab1.grid.addWidget(tab1.R1SNEdit, 3, 1)
        tab1.grid.addWidget(QLabel('R2 Serial Number'), 4, 1)
        tab1.grid.addWidget(tab1.R2SNEdit, 5, 1)
        tab1.grid.addWidget(QLabel('Applied Voltage'), 6, 1)
        tab1.grid.addWidget(tab1.AppVoltEdit, 7, 1)
        tab1.grid.addWidget(QLabel('N1 [Turns]'), 8, 1)
        tab1.grid.addWidget(tab1.N1Edit, 9, 1)
        tab1.grid.addWidget(QLabel('Meas. Cycles'), 10, 1)
        tab1.grid.addWidget(tab1.MeasCycEdit, 11, 1)
        tab1.grid.addWidget(QLabel('Full Cycle [s]'), 12, 1)
        tab1.grid.addWidget(tab1.FullCycEdit, 13, 1)
        tab1.grid.addWidget(QLabel('R1 Pressure [Pa]'), 14, 1)
        tab1.grid.addWidget(tab1.R1PresEdit, 15, 1)
        tab1.grid.addWidget(QLabel('R2 Pressure [Pa]'), 16, 1)
        tab1.grid.addWidget(tab1.R2PresEdit, 17, 1)
        tab1.grid.addWidget(QLabel('Comments'), 18, 1)
        tab1.grid.addWidget(tab1.CommentsTextBrowser, 19, 1)
        tab1.grid.addWidget(QLabel('.txtFile'), 20, 1)
        tab1.grid.addWidget(tab1.txtFileEdit, 21, 1)
        tab1.grid.addWidget(QLabel('Magnicon Electronics'), 22, 1)
        tab1.grid.addWidget(tab1.MagElecSpinBox, 23, 1)
        tab1.grid.addWidget(QLabel('Probe'), 24, 1)
        tab1.grid.addWidget(tab1.ProbeSpinBox, 25, 1)

        tab1.grid.addWidget(QLabel(f'R1 [{chr(956)}{chr(937)}/{chr(937)}]'), 2, 3)
        tab1.grid.addWidget(tab1.R1PPMEdit, 3, 3)
        tab1.grid.addWidget(QLabel(f'R2 [{chr(956)}{chr(937)}/{chr(937)}]'), 4, 3)
        tab1.grid.addWidget(tab1.R2PPMEdit, 5, 3)
        tab1.grid.addWidget(QLabel('I1 [A]'), 6, 3)
        tab1.grid.addWidget(tab1.I1Edit, 7, 3)
        tab1.grid.addWidget(QLabel('N2 [Turns]'), 8, 3)
        tab1.grid.addWidget(tab1.N2Edit, 9, 3)
        tab1.grid.addWidget(QLabel('Sample Half Cycle'), 10, 3)
        tab1.grid.addWidget(tab1.SHCEdit, 11, 3)
        tab1.grid.addWidget(QLabel('Ramp [s]'), 12, 3)
        tab1.grid.addWidget(tab1.RampEdit, 13, 3)
        tab1.grid.addWidget(QLabel('R1 Oil Depth [mm]'), 14, 3)
        tab1.grid.addWidget(tab1.R1OilDepthSpinBox, 15, 3)
        tab1.grid.addWidget(QLabel('R2 Oil Depth [mm]'), 16, 3)
        tab1.grid.addWidget(tab1.R2OilDepthSpinBox, 17, 3)


        tab1.setLayout(tab1.grid)

        return tab1

    def tab1_edits(self, tab1):
        # Column 1
        tab1.R1SNEdit = QLineEdit(tab1)
        tab1.R1SNEdit.setReadOnly(True)
        tab1.R2SNEdit = QLineEdit(tab1)
        tab1.R2SNEdit.setReadOnly(True)
        tab1.AppVoltEdit = QLineEdit(tab1)
        tab1.AppVoltEdit.setReadOnly(True)
        tab1.N1Edit = QLineEdit(tab1)
        tab1.N1Edit.setReadOnly(True)
        tab1.MeasCycEdit = QLineEdit(tab1)
        tab1.MeasCycEdit.setReadOnly(True)
        tab1.FullCycEdit = QLineEdit(tab1)
        tab1.FullCycEdit.setReadOnly(True)
        tab1.R1PresEdit = QLineEdit(tab1)
        tab1.R1PresEdit.setReadOnly(True)
        tab1.R2PresEdit = QLineEdit(tab1)
        tab1.R2PresEdit.setReadOnly(True)
        tab1.CommentsTextBrowser = QTextBrowser(tab1)
        tab1.CommentsTextBrowser.setReadOnly(False)
        tab1.txtFileEdit = QLineEdit(tab1)
        tab1.MagElecSpinBox = QComboBox(tab1)
        tab1.MagElecSpinBox.addItem('CCC2014-01')
        tab1.MagElecSpinBox.addItem('CCC2019-01')
        tab1.ProbeSpinBox = QComboBox(tab1)
        tab1.ProbeSpinBox.addItem('Magnicon1')
        tab1.ProbeSpinBox.addItem('NIST1')
        # Column 3
        tab1.R1PPMEdit = QLineEdit(tab1)
        tab1.R1PPMEdit.setReadOnly(True)
        tab1.R2PPMEdit = QLineEdit(tab1)
        tab1.R2PPMEdit.setReadOnly(True)
        tab1.I1Edit = QLineEdit(tab1)
        tab1.I1Edit.setReadOnly(True)
        tab1.N2Edit = QLineEdit(tab1)
        tab1.N2Edit.setReadOnly(True)
        tab1.SHCEdit = QLineEdit(tab1)
        tab1.SHCEdit.setReadOnly(True)
        tab1.RampEdit = QLineEdit(tab1)
        tab1.RampEdit.setReadOnly(True)
        tab1.R1OilDepthSpinBox = QSpinBox(tab1)
        tab1.R2OilDepthSpinBox = QSpinBox(tab1)



        return tab1

    def tab2UI(self, tab2):
        return tab2

    def tab3UI(self, tab3):
        return tab3


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()