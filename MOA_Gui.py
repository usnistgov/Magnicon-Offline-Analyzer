from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from magnicon_ccc import magnicon_ccc
from create_mag_ccc_datafile import writeDataFile
import sys, os

bp = os.getcwd()
if os.path.exists(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\Ali\py\ResDatabase'):
    sys.path.append(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\Ali\py\ResDatabase')
    from ResDataBase import ResData
else:
    os.chdir('..')
    os.chdir('ResDatabase')
    ResDataDir = os.getcwd()
    os.chdir('..')
    os.chdir('Magnicon-Offline-Analyzer')
    sys.path.append(ResDataDir)
    from ResDataBase import ResData

from bvd_stats import bvd_stat
from skew_and_kurt import skewness, kurtosis
import tkinter
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter, NullFormatter
from allan_variance import allan
import numpy as np

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tabs = QTabWidget(self)
        # self.tabs.addTab(self, 'Settings/Results')
        # self.tabs.addTab(self, 'BVD')        
        # self.tabs.addTab(self, 'Allan Dev.')



        self.setWindowTitle('Magnicon Offline Analyzer')
        self.setWindowIcon(QIcon('analyzer.ico'))


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()