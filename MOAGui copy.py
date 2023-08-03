from PyQt6.QtWidgets import *
from PyQt6.QtCore import QRect, QMetaObject, QCoreApplication
from PyQt6.QtGui import QIcon
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
# from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter, MaxNLocator
from allan_deviation import allan
from numpy import sqrt, std, ones

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        mainWindow.resize(989, 833)
        mainWindow.setWindowIcon(QIcon('analyzer.ico'))

        self.initializations()

        self.centralwidget = QWidget(parent=mainWindow)
        self.tabWidget = QTabWidget(parent=self.centralwidget)
        self.tabWidget.setGeometry(QRect(0, 0, 961, 791))
        self.SetResTab = QWidget()
        self.tabWidget.addTab(self.SetResTab, "")

        self.setLabels()
        self.setLineEdits()
        self.setSpinBoxes()
        self.setComboBoxes()
        self.setMisc()
        self.setButtons()
        self.BVDTabSetUp()
        self.AllanTabSetUp()
        self.SpecTabSetUp()

        self.tabWidget.currentChanged.connect(self.tabIndexChanged)
        
        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(parent=mainWindow)
        self.menubar.setGeometry(QRect(0, 0, 954, 22))
        mainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(parent=mainWindow)
        mainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(mainWindow)
        self.tabWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(mainWindow)

    def initializations(self):
        # try:
        #     self.R = ResData(r'\\elwood.nist.gov\68_PML\68internal\Calibrations\MDSS Data\resist\vax_data\resistor data\ARMS\Analysis Files')
        # except FileNotFoundError:
        #     self.R = ResData(ResDataDir)
        self.R = ResData(bp)
        self.validFile = False
        self.txtFilePath = ''
        self.plottedBVD = False
        self.plottedAllan = False
        self.plottedSpec = False
        self.data = False

        self.R1Temp = 25.0000
        self.R2Temp = 25.0000
        self.R1pres = 101325
        self.R2pres = 101325
        self.R1OilDepth = 203
        self.R2OilDepth = 203

        self.RButStatus = 'R1'
        self.SquidFeedStatus = 'NEG'
        self.CurrentButStatus = 'I1'
        self.saveStatus = False

        self.bvdCount = []
        self.deletedIndex = []
        self.deletedCount = []
        self.deletedBVD = []
        self.deletedR1 = []
        self.deletedR2 = []

    # Set up for the labels
    def setLabels(self):
        self.R1OilDepthLabel = QLabel(parent=self.SetResTab)
        self.R1OilDepthLabel.setGeometry(QRect(130, 390, 101, 16))
        self.R2OilDepthLabel = QLabel(parent=self.SetResTab)
        self.R2OilDepthLabel.setGeometry(QRect(130, 450, 101, 16))
        self.RelHumLabel = QLabel(parent=self.SetResTab)
        self.RelHumLabel.setGeometry(QRect(440, 450, 121, 16))
        self.R2TempLabel = QLabel(parent=self.SetResTab)
        self.R2TempLabel.setGeometry(QRect(440, 390, 111, 16))
        self.R1PresLabel = QLabel(parent=self.SetResTab)
        self.R1PresLabel.setGeometry(QRect(20, 390, 91, 16))
        self.R2PresLabel = QLabel(parent=self.SetResTab)
        self.R2PresLabel.setGeometry(QRect(20, 450, 91, 16))
        self.MagElecLabel = QLabel(parent=self.SetResTab)
        self.MagElecLabel.setGeometry(QRect(20, 660, 121, 16))
        self.R1OilPresLabel = QLabel(parent=self.SetResTab)
        self.R1OilPresLabel.setGeometry(QRect(280, 390, 111, 16))
        self.R2OilPresLabel = QLabel(parent=self.SetResTab)
        self.R2OilPresLabel.setGeometry(QRect(280, 450, 111, 16))
        self.R1TempLabel = QLabel(parent=self.SetResTab)
        self.R1TempLabel.setGeometry(QRect(440, 330, 111, 16))
        self.StandardRLabel = QLabel(parent=self.SetResTab)
        self.StandardRLabel.setGeometry(QRect(460, 510, 71, 16))
        self.MeasTimeLabel = QLabel(parent=self.SetResTab)
        self.MeasTimeLabel.setGeometry(QRect(440, 90, 111, 16))
        self.RemTimeLabel = QLabel(parent=self.SetResTab)
        self.RemTimeLabel.setGeometry(QRect(440, 150, 91, 16))
        self.ReadingDelayLabel = QLabel(parent=self.SetResTab)
        self.ReadingDelayLabel.setGeometry(QRect(440, 30, 91, 16))
        self.SquidFeedLabel = QLabel(parent=self.SetResTab)
        self.SquidFeedLabel.setGeometry(QRect(460, 660, 81, 16))
        self.R1TotalPresLabel = QLabel(parent=self.SetResTab)
        self.R1TotalPresLabel.setGeometry(QRect(440, 210, 111, 16))
        self.R2TotalPresLabel = QLabel(parent=self.SetResTab)
        self.R2TotalPresLabel.setGeometry(QRect(440, 270, 111, 16))
        self.VMeanLabel = QLabel(parent=self.SetResTab)
        self.VMeanLabel.setGeometry(QRect(630, 30, 49, 16))
        self.RMeanChkPPMLabel = QLabel(parent=self.SetResTab)
        self.RMeanChkPPMLabel.setGeometry(QRect(740, 330, 101, 16))
        self.C2Label = QLabel(parent=self.SetResTab)
        self.C2Label.setGeometry(QRect(630, 270, 51, 16))
        self.StdDevMeanLabel = QLabel(parent=self.SetResTab)
        self.StdDevMeanLabel.setGeometry(QRect(630, 150, 81, 16))
        self.R1STPLabel = QLabel(parent=self.SetResTab)
        self.R1STPLabel.setGeometry(QRect(850, 90, 81, 16))
        self.R2STPLabel = QLabel(parent=self.SetResTab)
        self.R2STPLabel.setGeometry(QRect(850, 30, 81, 16))
        self.C1Label = QLabel(parent=self.SetResTab)
        self.C1Label.setGeometry(QRect(630, 210, 49, 16))
        self.StdDevC2Label = QLabel(parent=self.SetResTab)
        self.StdDevC2Label.setGeometry(QRect(740, 270, 101, 16))
        self.StdDevC1Label = QLabel(parent=self.SetResTab)
        self.StdDevC1Label.setGeometry(QRect(740, 210, 101, 16))
        self.RatioMeanLabel = QLabel(parent=self.SetResTab)
        self.RatioMeanLabel.setGeometry(QRect(700, 510, 61, 16))
        self.ppmMeanLabel = QLabel(parent=self.SetResTab)
        self.ppmMeanLabel.setGeometry(QRect(630, 330, 71, 16))
        self.C1C2Label = QLabel(parent=self.SetResTab)
        self.C1C2Label.setGeometry(QRect(740, 450, 71, 16))
        self.StdDevMeanPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevMeanPPMLabel.setGeometry(QRect(630, 450, 91, 16))
        self.StdDevLabel = QLabel(parent=self.SetResTab)
        self.StdDevLabel.setGeometry(QRect(630, 90, 51, 16))
        self.StdDevPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevPPMLabel.setGeometry(QRect(630, 390, 81, 16))
        self.NLabel = QLabel(parent=self.SetResTab)
        self.NLabel.setGeometry(QRect(850, 150, 16, 16))
        self.StdDevChkPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevChkPPMLabel.setGeometry(QRect(740, 390, 101, 16))
        self.NAuxLabel = QLabel(parent=self.SetResTab)
        self.NAuxLabel.setGeometry(QRect(300, 210, 71, 16))
        self.SHCLabel = QLabel(parent=self.SetResTab)
        self.SHCLabel.setGeometry(QRect(160, 270, 101, 16))
        self.DelayLabel = QLabel(parent=self.SetResTab)
        self.DelayLabel.setGeometry(QRect(340, 330, 49, 16))
        self.N2Label = QLabel(parent=self.SetResTab)
        self.N2Label.setGeometry(QRect(160, 210, 61, 16))
        self.R2ValueLabel = QLabel(parent=self.SetResTab)
        self.R2ValueLabel.setGeometry(QRect(300, 90, 49, 16))
        self.N1Label = QLabel(parent=self.SetResTab)
        self.N1Label.setGeometry(QRect(20, 210, 61, 16))
        self.Current1Label = QLabel(parent=self.SetResTab)
        self.Current1Label.setGeometry(QRect(160, 150, 31, 16))
        self.FullCycLabel = QLabel(parent=self.SetResTab)
        self.FullCycLabel.setGeometry(QRect(20, 330, 71, 16))
        self.Current2Label = QLabel(parent=self.SetResTab)
        self.Current2Label.setGeometry(QRect(300, 150, 31, 16))
        self.MeasCycLabel = QLabel(parent=self.SetResTab)
        self.MeasCycLabel.setGeometry(QRect(20, 270, 81, 16))
        self.R1SNLabel = QLabel(parent=self.SetResTab)
        self.R1SNLabel.setGeometry(QRect(20, 30, 101, 16))
        self.R2SNLabel = QLabel(parent=self.SetResTab)
        self.R2SNLabel.setGeometry(QRect(20, 90, 101, 16))
        self.RampLabel = QLabel(parent=self.SetResTab)
        self.RampLabel.setGeometry(QRect(130, 330, 49, 16))
        self.R1PPMLabel = QLabel(parent=self.SetResTab)
        self.R1PPMLabel.setGeometry(QRect(160, 30, 59, 16))
        self.R2PPMLabel = QLabel(parent=self.SetResTab)
        self.R2PPMLabel.setGeometry(QRect(160, 90, 59, 16))
        self.R1ValueLabel = QLabel(parent=self.SetResTab)
        self.R1ValueLabel.setGeometry(QRect(300, 30, 49, 16))
        self.AppVoltLabel = QLabel(parent=self.SetResTab)
        self.AppVoltLabel.setGeometry(QRect(20, 150, 101, 16))
        self.MeasLabel = QLabel(parent=self.SetResTab)
        self.MeasLabel.setGeometry(QRect(230, 330, 49, 16))
        self.SampUsedLabel = QLabel(parent=self.SetResTab)
        self.SampUsedLabel.setGeometry(QRect(300, 270, 81, 16))
        self.ResultsLabel = QLabel(parent=self.SetResTab)
        self.ResultsLabel.setGeometry(QRect(760, 10, 41, 16))
        self.SettingsLabel = QLabel(parent=self.SetResTab)
        self.SettingsLabel.setGeometry(QRect(260, 10, 49, 16))
        self.CommentsLabel = QLabel(parent=self.SetResTab)
        self.CommentsLabel.setGeometry(QRect(20, 510, 61, 16))
        self.txtFileLabel = QLabel(parent=self.SetResTab)
        self.txtFileLabel.setGeometry(QRect(20, 600, 41, 16))
        self.VMeanChkLabel = QLabel(parent=self.SetResTab)
        self.VMeanChkLabel.setGeometry(QRect(740, 30, 81, 16))
        self.StdDevChkLabel = QLabel(parent=self.SetResTab)
        self.StdDevChkLabel.setGeometry(QRect(740, 90, 81, 16))
        self.StdDevMeanChkLabel = QLabel(parent=self.SetResTab)
        self.StdDevMeanChkLabel.setGeometry(QRect(740, 150, 111, 16))
        self.MDSSLabel = QLabel(parent=self.SetResTab)
        self.MDSSLabel.setGeometry(QRect(630, 600, 61, 16))
        self.ProbeLabel = QLabel(parent=self.SetResTab)
        self.ProbeLabel.setGeometry(QRect(20, 710, 31, 16))
        self.CurrentButLabel = QLabel(parent=self.SetResTab)
        self.CurrentButLabel.setGeometry(QRect(470, 710, 51, 16))

    # Set up the read only LineEdits
    def setLineEdits(self):
        self.R1TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TotalPresLineEdit.setGeometry(QRect(440, 230, 113, 22))
        self.R1TotalPresLineEdit.setReadOnly(True)
        self.R2TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TotalPresLineEdit.setGeometry(QRect(440, 290, 113, 22))
        self.R2TotalPresLineEdit.setReadOnly(True)
        self.RMeanChkPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.RMeanChkPPMLineEdit.setGeometry(QRect(740, 350, 81, 22))
        self.RMeanChkPPMLineEdit.setStyleSheet("")
        self.RMeanChkPPMLineEdit.setReadOnly(True)
        self.C1C2LineEdit = QLineEdit(parent=self.SetResTab)
        self.C1C2LineEdit.setGeometry(QRect(740, 470, 81, 22))
        self.C1C2LineEdit.setStyleSheet("")
        self.C1C2LineEdit.setReadOnly(True)
        self.StdDevLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevLineEdit.setGeometry(QRect(630, 110, 81, 22))
        self.StdDevLineEdit.setReadOnly(True)
        self.StdDevMeanPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanPPMLineEdit.setGeometry(QRect(630, 470, 81, 22))
        self.StdDevMeanPPMLineEdit.setStyleSheet("")
        self.StdDevMeanPPMLineEdit.setReadOnly(True)
        self.VMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanLineEdit.setGeometry(QRect(630, 50, 81, 22))
        self.VMeanLineEdit.setReadOnly(True)
        self.StdDevPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevPPMLineEdit.setGeometry(QRect(630, 410, 81, 22))
        self.StdDevPPMLineEdit.setStyleSheet("")
        self.StdDevPPMLineEdit.setReadOnly(True)
        self.R2STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2STPLineEdit.setGeometry(QRect(850, 50, 81, 22))
        self.R2STPLineEdit.setReadOnly(True)
        self.C1LineEdit = QLineEdit(parent=self.SetResTab)
        self.C1LineEdit.setGeometry(QRect(630, 230, 81, 22))
        self.C1LineEdit.setStyleSheet("")
        self.C1LineEdit.setReadOnly(True)
        self.StdDevMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanLineEdit.setGeometry(QRect(630, 170, 81, 22))
        self.StdDevMeanLineEdit.setReadOnly(True)
        self.RatioMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.RatioMeanLineEdit.setGeometry(QRect(630, 530, 191, 22))
        self.RatioMeanLineEdit.setStyleSheet("")
        self.RatioMeanLineEdit.setReadOnly(True)
        self.ppmMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.ppmMeanLineEdit.setGeometry(QRect(630, 350, 81, 22))
        self.ppmMeanLineEdit.setStyleSheet("")
        self.ppmMeanLineEdit.setReadOnly(True)
        self.StdDevC2LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC2LineEdit.setGeometry(QRect(740, 290, 81, 22))
        self.StdDevC2LineEdit.setStyleSheet("")
        self.StdDevC2LineEdit.setReadOnly(True)
        self.R1STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1STPLineEdit.setGeometry(QRect(850, 110, 81, 22))
        self.R1STPLineEdit.setReadOnly(True)
        self.StdDevChkPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkPPMLineEdit.setGeometry(QRect(740, 410, 81, 22))
        self.StdDevChkPPMLineEdit.setStyleSheet("")
        self.StdDevChkPPMLineEdit.setReadOnly(True)
        self.StdDevC1LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC1LineEdit.setGeometry(QRect(740, 230, 81, 22))
        self.StdDevC1LineEdit.setStyleSheet("")
        self.StdDevC1LineEdit.setReadOnly(True)
        self.C2LineEdit = QLineEdit(parent=self.SetResTab)
        self.C2LineEdit.setGeometry(QRect(630, 290, 81, 22))
        self.C2LineEdit.setStyleSheet("")
        self.C2LineEdit.setReadOnly(True)
        self.NLineEdit = QLineEdit(parent=self.SetResTab)
        self.NLineEdit.setGeometry(QRect(850, 170, 81, 22))
        self.NLineEdit.setReadOnly(True)
        self.Current1LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current1LineEdit.setGeometry(QRect(160, 170, 113, 22))
        self.Current1LineEdit.setReadOnly(True)
        self.FullCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.FullCycLineEdit.setGeometry(QRect(20, 350, 71, 22))
        self.FullCycLineEdit.setReadOnly(True)
        self.MeasLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasLineEdit.setGeometry(QRect(230, 350, 71, 22))
        self.MeasLineEdit.setReadOnly(True)
        self.SampUsedLineEdit = QLineEdit(parent=self.SetResTab)
        self.SampUsedLineEdit.setGeometry(QRect(300, 290, 113, 22))
        self.SampUsedLineEdit.setReadOnly(True)
        self.R1SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1SNLineEdit.setGeometry(QRect(20, 50, 113, 22))
        self.R1SNLineEdit.setReadOnly(True)
        self.Current2LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current2LineEdit.setGeometry(QRect(300, 170, 113, 22))
        self.Current2LineEdit.setReadOnly(True)
        self.N2LineEdit = QLineEdit(parent=self.SetResTab)
        self.N2LineEdit.setGeometry(QRect(160, 230, 113, 22))
        self.N2LineEdit.setReadOnly(True)
        self.NAuxLineEdit = QLineEdit(parent=self.SetResTab)
        self.NAuxLineEdit.setGeometry(QRect(300, 230, 113, 22))
        self.NAuxLineEdit.setReadOnly(True)
        self.R2PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PPMLineEdit.setGeometry(QRect(160, 110, 113, 22))
        self.R2PPMLineEdit.setReadOnly(True)
        self.R2ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2ValueLineEdit.setGeometry(QRect(300, 110, 113, 22))
        self.R2ValueLineEdit.setReadOnly(True)
        self.MeasCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasCycLineEdit.setGeometry(QRect(20, 290, 113, 22))
        self.MeasCycLineEdit.setReadOnly(True)
        self.AppVoltLineEdit = QLineEdit(parent=self.SetResTab)
        self.AppVoltLineEdit.setGeometry(QRect(20, 170, 113, 22))
        self.AppVoltLineEdit.setReadOnly(True)
        self.DelayLineEdit = QLineEdit(parent=self.SetResTab)
        self.DelayLineEdit.setGeometry(QRect(340, 350, 71, 22))
        self.DelayLineEdit.setReadOnly(True)
        self.R1PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1PPMLineEdit.setGeometry(QRect(160, 50, 113, 22))
        self.R1PPMLineEdit.setReadOnly(True)
        self.RampLineEdit = QLineEdit(parent=self.SetResTab)
        self.RampLineEdit.setGeometry(QRect(130, 350, 71, 22))
        self.RampLineEdit.setReadOnly(True)
        self.R2SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2SNLineEdit.setGeometry(QRect(20, 110, 113, 22))
        self.R2SNLineEdit.setReadOnly(True)
        self.SHCLineEdit = QLineEdit(parent=self.SetResTab)
        self.SHCLineEdit.setGeometry(QRect(160, 290, 113, 22))
        self.SHCLineEdit.setReadOnly(True)
        self.N1LineEdit = QLineEdit(parent=self.SetResTab)
        self.N1LineEdit.setGeometry(QRect(20, 230, 113, 22))
        self.N1LineEdit.setReadOnly(True)
        self.R1ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1ValueLineEdit.setGeometry(QRect(300, 50, 113, 22))
        self.R1ValueLineEdit.setReadOnly(True)
        self.MeasTimeLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasTimeLineEdit.setGeometry(QRect(440, 110, 113, 22))
        self.MeasTimeLineEdit.setReadOnly(True)
        self.RemTimeLineEdit = QLineEdit(parent=self.SetResTab)
        self.RemTimeLineEdit.setGeometry(QRect(440, 170, 113, 22))
        self.RemTimeLineEdit.setReadOnly(True)

        self.R2OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2OilPresLineEdit.setGeometry(QRect(280, 470, 111, 22))
        self.R2OilPresLineEdit.setReadOnly(True)

        self.VMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanChkLineEdit.setGeometry(QRect(740, 50, 81, 22))
        self.VMeanChkLineEdit.setReadOnly(True)
        self.StdDevChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkLineEdit.setGeometry(QRect(740, 110, 81, 22))
        self.StdDevChkLineEdit.setReadOnly(True)
        self.StdDevMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanChkLineEdit.setGeometry(QRect(740, 170, 81, 22))
        self.StdDevMeanChkLineEdit.setReadOnly(True)

        self.R1OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1OilPresLineEdit.setGeometry(QRect(280, 410, 111, 22))
        self.R1OilPresLineEdit.setReadOnly(True)
        self.RelHumLineEdit = QLineEdit(parent=self.SetResTab)
        self.RelHumLineEdit.setGeometry(QRect(440, 470, 113, 22))
        self.R1TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TempLineEdit.setGeometry(QRect(440, 350, 113, 22))
        self.R1TempLineEdit.returnPressed.connect(self.temp1Changed)
        self.R1PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1PresLineEdit.setGeometry(QRect(20, 410, 81, 22))
        self.R1PresLineEdit.returnPressed.connect(self.R1PresChanged)
        self.R2PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PresLineEdit.setGeometry(QRect(20, 470, 81, 22))
        self.R2PresLineEdit.returnPressed.connect(self.R2PresChanged)
        self.R2TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TempLineEdit.setGeometry(QRect(440, 410, 113, 22))
        self.R2TempLineEdit.returnPressed.connect(self.temp2Changed)

        self.txtFileLineEdit = QLineEdit(parent=self.SetResTab)
        self.txtFileLineEdit.setGeometry(QRect(20, 620, 511, 22))
        self.txtFileLineEdit.returnPressed.connect(self.folderEdited)

    def BVDTabSetUp(self):
        self.BVDTab = QWidget()
        self.tabWidget.addTab(self.BVDTab, "")
        self.BVDVerticalLayoutWidget = QWidget(parent=self.BVDTab)
        self.BVDVerticalLayoutWidget.setGeometry(QRect(0, 0, 951, 681))
        self.BVDVerticalLayout = QVBoxLayout(self.BVDVerticalLayoutWidget)

        # self.fig = plt.figure(figsize=(1,1),dpi=100)
        self.BVDfig = plt.figure()
        self.BVDax1 = self.BVDfig.add_subplot(2,1,1)
        self.BVDax2 = self.BVDfig.add_subplot(2,2,3)
        self.BVDax3 = self.BVDfig.add_subplot(2,2,4)
        self.BVDax1.tick_params(direction='in')
        self.BVDax2.tick_params(direction='in')
        self.BVDax3.tick_params(direction='in')
        self.BVDcanvas = FigureCanvas(self.BVDfig)
        self.BVDVerticalLayout.addWidget(NavigationToolbar(self.BVDcanvas))
        self.BVDVerticalLayout.addWidget(self.BVDcanvas)

        gridWidget = QWidget(self.BVDTab)
        gridWidget.setGeometry(QRect(0, 680, 951, 81))
        grid = QGridLayout(gridWidget)
        grid.setSpacing(5)

        #
        self.deletePlotBut = QPushButton()
        self.deletePlotBut.setText('Delete')
        self.deletePlotBut.pressed.connect(self.deleteBut)
        self.plotCountCombo = QComboBox()
        self.RestoreBut = QPushButton()
        self.RestoreBut.setText('Restore Last')
        self.RestoreBut.pressed.connect(self.restoreDeleted)
        self.RePlotBut = QPushButton()
        self.RePlotBut.setText('Replot All')
        self.RePlotBut.pressed.connect(self.replotAll)

        #
        SkewnessLabel = QLabel('Skewness', parent=gridWidget)
        KurtosisLabel = QLabel('Kurtosis', parent=gridWidget)
        self.SkewnessEdit = QLineEdit(gridWidget)
        self.SkewnessEdit.setReadOnly(True)
        self.KurtosisEdit = QLineEdit(gridWidget)
        self.KurtosisEdit.setReadOnly(True)
        Spacer1 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        Spacer2 = QSpacerItem(600, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        #
        grid.addWidget(self.deletePlotBut, 1, 1)
        grid.addWidget(self.plotCountCombo, 2, 1)
        grid.addItem(Spacer1, 1, 2)
        grid.addItem(Spacer1, 2, 2)
        grid.addWidget(self.RestoreBut, 1, 3)
        grid.addWidget(self.RePlotBut, 2, 3)
        grid.addItem(Spacer2, 1, 4)
        grid.addItem(Spacer2, 2, 4)
        grid.addWidget(SkewnessLabel, 1, 5)
        grid.addWidget(self.SkewnessEdit, 2, 5)
        grid.addItem(Spacer1, 1, 6)
        grid.addItem(Spacer1, 2, 6)
        grid.addWidget(KurtosisLabel, 1, 7)
        grid.addWidget(self.KurtosisEdit, 2, 7)

    def AllanTabSetUp(self):
        self.AllanTab = QWidget()
        self.tabWidget.addTab(self.AllanTab, "")
        self.AllanVerticalLayoutWidget = QWidget(parent=self.AllanTab)
        self.AllanVerticalLayoutWidget.setGeometry(QRect(0, 0, 951, 761))
        self.AllanVerticalLayout = QVBoxLayout(self.AllanVerticalLayoutWidget)
        
        self.Allanfig = plt.figure()
        self.Allanax1 = self.Allanfig.add_subplot(2,2,1)
        self.Allanax2 = self.Allanfig.add_subplot(2,2,2)
        self.Allanax3 = self.Allanfig.add_subplot(2,2,3)
        self.Allanax4 = self.Allanfig.add_subplot(2,2,4)
        self.Allanax1.tick_params(axis='both', which='both', direction='in')
        self.Allanax2.tick_params(direction='in')
        self.Allanax3.tick_params(direction='in')
        self.Allanax4.tick_params(direction='in')
        self.AllanCanvas = FigureCanvas(self.Allanfig)
        self.AllanVerticalLayout.addWidget(NavigationToolbar(self.AllanCanvas))
        self.AllanVerticalLayout.addWidget(self.AllanCanvas)

        self.AllanHorizontalLayout = QHBoxLayout()

        self.AllanTypeComboBox = QComboBox(parent=self.AllanTab)
        self.AllanTypeComboBox.setEditable(False)
        self.AllanTypeComboBox.addItem('all')
        self.AllanTypeComboBox.addItem('2^n')
        self.AllanTypeComboBox.currentIndexChanged.connect(self.plotAllan)

        self.OverlappingComboBox = QComboBox(parent=self.AllanTab)
        self.OverlappingComboBox.setEditable(False)
        self.OverlappingComboBox.addItem('non-overlapping')
        self.OverlappingComboBox.addItem('overlapping')
        self.OverlappingComboBox.currentIndexChanged.connect(self.plotAllan)

        self.AllanHorizontalSpacer = QSpacerItem(600, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.AllanHorizontalLayout.addWidget(self.AllanTypeComboBox)
        self.AllanHorizontalLayout.addItem(self.AllanHorizontalSpacer)
        self.AllanHorizontalLayout.addWidget(self.OverlappingComboBox)
        self.AllanVerticalLayout.addLayout(self.AllanHorizontalLayout)

    def SpecTabSetUp(self):
        self.SpecTab = QWidget()
        self.tabWidget.addTab(self.SpecTab, "")
        self.SpecVerticalLayoutWidget = QWidget(parent=self.SpecTab)
        self.SpecVerticalLayoutWidget.setGeometry(QRect(0, 0, 951, 761))
        self.SpecVerticalLayout = QVBoxLayout(self.SpecVerticalLayoutWidget)

        self.Specfig = plt.figure()
        self.SpecAx = self.Specfig.add_subplot(2,1,1)
        self.SpecAx.tick_params(direction='in')
        self.PowerSpecAx = self.Specfig.add_subplot(2,1,2)
        self.PowerSpecAx.tick_params(direction='in')
        self.SpecCanvas = FigureCanvas(self.Specfig)
        self.SpecVerticalLayout.addWidget(NavigationToolbar(self.SpecCanvas))
        self.SpecVerticalLayout.addWidget(self.SpecCanvas)

    def setButtons(self):
        self.StandardRBut = QPushButton(parent=self.SetResTab)
        self.StandardRBut.setGeometry(QRect(460, 530, 71, 24))
        self.StandardRBut.setStyleSheet("color: white; background-color: red")
        self.StandardRBut.clicked.connect(self.RButClicked)

        self.SquidFeedBut = QPushButton(parent=self.SetResTab)
        self.SquidFeedBut.setGeometry(QRect(440, 680, 111, 24))
        self.SquidFeedBut.setStyleSheet("color: white; background-color: blue")
        self.SquidFeedBut.clicked.connect(self.SquidButClicked)

        self.CurrentBut = QPushButton(parent=self.SetResTab)
        self.CurrentBut.setGeometry(QRect(440, 730, 111, 24))
        self.CurrentBut.setStyleSheet("color: white; background-color: red")
        self.CurrentBut.clicked.connect(self.CurrentButClicked)

        self.MDSSButton = QPushButton(parent=self.SetResTab)
        self.MDSSButton.setGeometry(QRect(630, 620, 75, 24))
        # self.MDSSButton.setStyleSheet("color: white; background-color: red")
        self.MDSSButton.setEnabled(False)
        self.MDSSButton.clicked.connect(self.MDSSClicked)
        
        self.saveButton = QPushButton(parent=self.SetResTab)
        self.saveButton.setGeometry(QRect(630, 680, 75, 24))
        self.saveButton.setEnabled(False)
        self.saveButton.clicked.connect(self.saveMDSS)
                
        self.folderToolButton = QToolButton(parent=self.SetResTab)
        self.folderToolButton.setGeometry(QRect(530, 620, 22, 22))
        self.folderToolButton.setIcon(QIcon(bp + r'\folder.ico'))
        self.folderToolButton.clicked.connect(self.folderClicked)

    def setSpinBoxes(self):
        self.ReadingDelaySpinBox = QSpinBox(parent=self.SetResTab)
        self.ReadingDelaySpinBox.setGeometry(QRect(440, 50, 113, 22))
        self.R1OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R1OilDepthSpinBox.setGeometry(QRect(130, 410, 101, 22))
        self.R1OilDepthSpinBox.setMaximum(10000)
        self.R2OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R2OilDepthSpinBox.setGeometry(QRect(130, 470, 101, 22))
        self.R2OilDepthSpinBox.setMaximum(10000)
        self.R1OilDepthSpinBox.valueChanged.connect(self.oilDepth1Changed)
        self.R2OilDepthSpinBox.valueChanged.connect(self.oilDepth2Changed)

    def setComboBoxes(self):
        self.MagElecComboBox = QComboBox(parent=self.SetResTab)
        self.MagElecComboBox.setGeometry(QRect(20, 680, 151, 22))
        self.MagElecComboBox.setEditable(False)
        self.MagElecComboBox.addItem('CCC2014-01')
        self.MagElecComboBox.addItem('CCC2019-01')

        self.ProbeComboBox = QComboBox(parent=self.SetResTab)
        self.ProbeComboBox.setGeometry(QRect(20, 730, 151, 22))
        self.ProbeComboBox.setEditable(False)
        self.ProbeComboBox.addItem('Magnicon1')
        self.ProbeComboBox.addItem('NIST1')

    def setMisc(self):
        self.SetResDivider = QFrame(parent=self.SetResTab)
        self.SetResDivider.setGeometry(QRect(580, -10, 20, 781))
        self.SetResDivider.setFrameShape(QFrame.Shape.VLine)
        self.SetResDivider.setFrameShadow(QFrame.Shadow.Sunken)

        self.CommentsTextBrowser = QTextBrowser(parent=self.SetResTab)
        self.CommentsTextBrowser.setGeometry(QRect(20, 530, 391, 51))
        self.CommentsTextBrowser.setReadOnly(False)

        self.progressBar = QProgressBar(parent=self.SetResTab)
        self.progressBar.setGeometry(QRect(740, 680, 111, 23))
        self.progressBar.setProperty("value", 0)

    def retranslateUi(self, mainWindow):
        _translate = QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "Magnicon Offline Analyzer"))
        self.R1OilDepthLabel.setText(_translate("mainWindow", "R1 Oil Depth [mm]"))
        self.RelHumLabel.setText(_translate("mainWindow", "Relative Humidity [%]"))
        self.R2TempLabel.setText(_translate("mainWindow", f'R2 Temperature [{chr(176)}C]'))
        self.R1PresLabel.setText(_translate("mainWindow", "R1 Pressure [Pa]"))
        self.MagElecLabel.setText(_translate("mainWindow", "Magnicon Electronics"))
        self.R1OilPresLabel.setText(_translate("mainWindow", "R1 Oil Pressure [Pa]"))
        self.R2OilPresLabel.setText(_translate("mainWindow", "R2 Oil Pressure [Pa]"))
        self.R1TempLabel.setText(_translate("mainWindow", f'R1 Temperature [{chr(176)}C]'))
        self.StandardRLabel.setText(_translate("mainWindow", "  Standard R"))
        self.MeasTimeLabel.setText(_translate("mainWindow", "Measurement Time"))
        self.RemTimeLabel.setText(_translate("mainWindow", "Remaining Time"))
        self.ReadingDelayLabel.setText(_translate("mainWindow", "Reading Delay [s]"))
        self.SquidFeedLabel.setText(_translate("mainWindow", "Squid Feed In"))
        self.StandardRBut.setText(_translate("mainWindow", "R1"))
        self.R1TotalPresLabel.setText(_translate("mainWindow", "R1 Total Pressure [Pa]"))
        self.VMeanLabel.setText(_translate("mainWindow", "Mean [V]"))
        self.RMeanChkPPMLabel.setText(_translate("mainWindow", "R Mean Chk (ppm)"))
        self.C2Label.setText(_translate("mainWindow", "C2 (ppm)"))
        self.StdDevMeanLabel.setText(_translate("mainWindow", "Std. Mean"))
        self.R1STPLabel.setText(_translate("mainWindow", "R1STPPredPPM"))
        self.R2STPLabel.setText(_translate("mainWindow", "R2STPPredPPM"))
        self.C1Label.setText(_translate("mainWindow", "C1 (ppm)"))
        self.StdDevC2Label.setText(_translate("mainWindow", "Std Dev C2 (ppm)"))
        self.StdDevC1Label.setText(_translate("mainWindow", "Std Dev C1 (ppm)"))
        self.RatioMeanLabel.setText(_translate("mainWindow", "Ratio Mean"))
        self.ppmMeanLabel.setText(_translate("mainWindow", "Mean (ppm)"))
        self.C1C2Label.setText(_translate("mainWindow", "C1-C2 (ppm)"))
        self.StdDevMeanPPMLabel.setText(_translate("mainWindow", "Std. Mean (ppm)"))
        self.StdDevLabel.setText(_translate("mainWindow", "Std. Dev."))
        self.StdDevPPMLabel.setText(_translate("mainWindow", "Std. Dev. (ppm)"))
        self.NLabel.setText(_translate("mainWindow", "N"))
        self.StdDevChkPPMLabel.setText(_translate("mainWindow", "Std. Dev. Chk (ppm)"))
        self.NAuxLabel.setText(_translate("mainWindow", "NAux [Turns]"))
        self.SHCLabel.setText(_translate("mainWindow", "Sample Half Cycle"))
        self.DelayLabel.setText(_translate("mainWindow", "Delay [s]"))
        self.N2Label.setText(_translate("mainWindow", "N2 [Turns]"))
        self.R2ValueLabel.setText(_translate("mainWindow", "R2 Value"))
        self.N1Label.setText(_translate("mainWindow", "N1 [Turns]"))
        self.Current1Label.setText(_translate("mainWindow", "I1 [A]"))
        self.FullCycLabel.setText(_translate("mainWindow", "Full Cycle [s]"))
        self.Current2Label.setText(_translate("mainWindow", "I2 [A]"))
        self.MeasCycLabel.setText(_translate("mainWindow", "Meas. Cycles"))
        self.R1SNLabel.setText(_translate("mainWindow", "R1 Serial Number"))
        self.R2SNLabel.setText(_translate("mainWindow", "R2 Serial Number"))
        self.RampLabel.setText(_translate("mainWindow", "Ramp [s]"))
        self.R1PPMLabel.setText(_translate("mainWindow", f'R1 [{chr(956)}{chr(937)}/{chr(937)}]'))
        self.R2PPMLabel.setText(_translate("mainWindow", f'R2 [{chr(956)}{chr(937)}/{chr(937)}]'))
        self.R1ValueLabel.setText(_translate("mainWindow", "R1 Value"))
        self.AppVoltLabel.setText(_translate("mainWindow", "Applied Voltage"))
        self.MeasLabel.setText(_translate("mainWindow", "Meas [s]"))
        self.SampUsedLabel.setText(_translate("mainWindow", "Samples Used"))
        self.ResultsLabel.setText(_translate("mainWindow", "Results"))
        self.SquidFeedBut.setText(_translate("mainWindow", "Negative"))
        self.SettingsLabel.setText(_translate("mainWindow", "Settings"))
        self.CommentsLabel.setText(_translate("mainWindow", "Comments"))
        self.R2TotalPresLabel.setText(_translate("mainWindow", "R2 Total Pressure [Pa]"))
        self.R2PresLabel.setText(_translate("mainWindow", "R2 Pressure [Pa]"))
        self.R2OilDepthLabel.setText(_translate("mainWindow", "R2 Oil Depth [mm]"))
        self.ProbeLabel.setText(_translate("mainWindow", "Probe"))
        self.CurrentButLabel.setText(_translate("mainWindow", "  Current"))
        self.CurrentBut.setText(_translate("mainWindow", "I1"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.BVDTab), _translate("mainWindow", "BVD"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.AllanTab), _translate("mainWindow", "Allan Dev."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SpecTab), _translate("mainWindow", "Spec/Power Spec."))
        self.txtFileLabel.setText(_translate("mainWindow", ".txt File"))
        self.VMeanChkLabel.setText(_translate("mainWindow", "Mean Chk [V]"))
        self.StdDevChkLabel.setText(_translate("mainWindow", "Std. Dev. Chk"))
        self.StdDevMeanChkLabel.setText(_translate("mainWindow", "Std. Mean Chk"))
        self.saveButton.setText(_translate("mainWindow", "Save"))
        self.MDSSButton.setText(_translate("mainWindow", "No"))
        self.MDSSLabel.setText(_translate("mainWindow", "Save MDSS"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))

    def plotBVD(self):
        if self.plottedBVD:
            self.clearPlots()

        self.plottedBVD = True

        count = range(len(self.bvd.A))
        self.BVDax1.scatter(count, self.bvd.A, color='r', marker='+', s=75)
        self.BVDax1.scatter(count, self.bvd.B, color='b', marker='x')
        self.BVDax1.set_title('Bridge Voltage')
        self.BVDax1.set_xlabel('Count')
        self.BVDax1.set_ylabel('Amplitude [V]')
        self.BVDax1.legend(['I+', 'I-'])

        # count = range(len(self.bvd.bvdList))
        if self.RButStatus == 'R1':
            self.BVDax2.scatter(self.bvdCount, self.bvd.R1List, color='b', zorder=3)
        else:
            self.BVDax2.scatter(self.bvdCount, self.bvd.R2List, color='b', zorder=3)

        self.BVDax2.set_title('BVD')
        self.BVDax2.set_xlabel('Count')
        if self.RButStatus == 'R1':
            self.BVDax2.set_ylabel('R2 [ppm]')
        else:
            self.BVDax2.set_ylabel('R1 [ppm]')

        self.BVDtwin2 = self.BVDax2.twinx()
        self.BVDtwin2.tick_params(direction='in')
        if self.bvd.bvdList:
            # self.BVDtwin2.plot(self.bvdCount, 3*self.bvd.std*ones(len(self.bvd.bvdList), dtype=int), color='r', linestyle='--')
            # self.BVDtwin2.plot(self.bvdCount, -3*self.bvd.std*ones(len(self.bvd.bvdList), dtype=int), color='r', linestyle='--')
            self.BVDtwin2.plot(self.bvdCount, 3*std(self.bvd.bvdList)*ones(len(self.bvd.bvdList), dtype=int), color='r', linestyle='--')
            self.BVDtwin2.plot(self.bvdCount, -3*std(self.bvd.bvdList)*ones(len(self.bvd.bvdList), dtype=int), color='r', linestyle='--')
            self.BVDtwin2.scatter(self.bvdCount, self.bvd.bvdList, color='r')
            # self.BVDtwin2.set_ylim([-3.2*self.bvd.std, 3.2*self.bvd.std])
            self.BVDtwin2.set_ylim([-3.2*std(self.bvd.bvdList), 3.2*std(self.bvd.bvdList)])

            self.BVDax3.hist(self.bvd.bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
            self.BVDax3.xaxis.set_major_locator(MaxNLocator(integer=True))
            # self.BVDax3.set_ylim([-3.2*self.bvd.std, 3.2*self.bvd.std])
            self.BVDax3.set_ylim([-3.2*std(self.bvd.bvdList), 3.2*std(self.bvd.bvdList)])
            self.BVDax3.set_title('BVD Histogram')
        else:
            self.BVDax2.cla()
            self.BVDax3.cla()

        self.BVDtwin2.set_ylabel('BVD [V]')
        self.BVDax2.set_axisbelow(True)
        self.BVDax2.grid(axis='x',zorder=0)
        self.BVDtwin2.set_axisbelow(True)
        self.BVDtwin2.grid(zorder=0)

        # self.BVDfig.tight_layout()
        self.BVDfig.set_tight_layout(True)
        self.BVDcanvas.draw()

        self.SkewnessEdit.setText(str("{:.3f}".format(skewness(self.bvd.bvdList))))
        self.KurtosisEdit.setText(str("{:.3f}".format(kurtosis(self.bvd.bvdList))))

    def plotAllan(self):
        if self.plottedAllan:
            self.clearPlots()
        
        self.plottedAllan = True
        allan_type = self.AllanTypeComboBox.currentText()
        overlapping = is_overlapping(self.OverlappingComboBox.currentText())

        self.Allanax1.set_xscale('log')
        self.Allanax1.xaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
        self.Allanax1.xaxis.set_minor_formatter(StrMethodFormatter('{x:.0f}'))
        self.Allanax1.set_yscale('log')

        # self.Allanax1.set_ylim([1E-9, 1E-8])
        if self.bvd.bvdList:
            bvd = allan(input_array=self.bvd.bvdList, allan_type=allan_type, overlapping=overlapping)
            C1 = allan(input_array=self.bvd.C1R1List, allan_type=allan_type, overlapping=overlapping)
            C2 = allan(input_array=self.bvd.C2R1List, allan_type=allan_type, overlapping=overlapping)
            I1 = allan(input_array=self.bvd.A, allan_type=allan_type, overlapping=overlapping)
            I2 = allan(input_array=self.bvd.B, allan_type=allan_type, overlapping=overlapping)

            self.Allanax1.plot(bvd.samples, bvd.tau_array)
            self.Allanax2.plot(C1.samples, C1.tau_array)
            self.Allanax3.plot(C2.samples, C2.tau_array)
            self.Allanax4.plot(I1.samples, I1.tau_array, color='b')
            self.Allanax4.plot(I2.samples, I2.tau_array, color='r')
        else:
            self.clearPlots()

        if self.validFile:
            self.Allanax1.set_title('Allan Deviation vs. Samples')
            self.Allanax1.set_ylabel('Allan Deviation')
            self.Allanax1.set_xlabel('\u03C4 (samples)')

            self.Allanax2.set_title('Allan Deviation of C1')
            self.Allanax2.set_ylabel('Allan Deviation')
            self.Allanax2.set_xlabel('\u03C4 (samples)')

            self.Allanax3.set_title('Allan Deviation of C2')
            self.Allanax3.set_ylabel('Allan Deviation')
            self.Allanax3.set_xlabel('\u03C4 (samples)')

            self.Allanax4.set_title('Allan Deviation of Bridge Voltage')
            self.Allanax4.set_ylabel('Allan Deviation')
            self.Allanax4.set_xlabel('\u03C4 (samples)')
            self.Allanax4.legend(['I+', 'I-'])

            self.Allanfig.set_tight_layout(True)
            self.AllanCanvas.draw()

    def plotSpec(self):
        if self.plottedSpec:
            self.clearPlots()

        # self.plottedSpec = True

        self.SpecAx.set_title('Power Spectrum')
        self.SpecAx.set_ylabel('Magnitude')
        self.SpecAx.set_xlabel('Frequency (Hz)')

        self.PowerSpecAx.set_title('Power Spectrum from FFT')
        self.PowerSpecAx.set_ylabel('Magnitude')
        self.PowerSpecAx.set_xlabel('Frequency (Hz)')

        self.Specfig.set_tight_layout(True)
        self.SpecCanvas.draw()

    def clearPlots(self):
        self.BVDax1.cla()
        self.BVDax2.cla()
        try:
            self.BVDtwin2.remove()
            self.BVDtwin2.set_visible(False)
        except (AttributeError, KeyError):
            pass
        self.BVDax3.cla()
        # self.fig.tight_layout()
        self.BVDcanvas.draw()

        self.Allanax1.cla()
        self.Allanax2.cla()
        self.Allanax3.cla()
        self.Allanax4.cla()
        self.AllanCanvas.draw()

    def RButClicked(self):
        if self.StandardRBut.pressed and self.RButStatus == 'R1':
            self.RButStatus = 'R2'
            self.StandardRBut.setText('R2')
            self.StandardRBut.setStyleSheet("color: white; background-color: green")
            if self.validFile:
                self.stdR(self.RButStatus)
        else:
            self.RButStatus = 'R1'
            self.StandardRBut.setText('R1')
            self.StandardRBut.setStyleSheet("color: white; background-color: red")
            if self.validFile:
                self.stdR(self.RButStatus)

    def SquidButClicked(self):
        if self.SquidFeedBut.pressed and self.SquidFeedStatus == 'NEG':
            self.SquidFeedStatus = 'POS'
            self.SquidFeedBut.setText('Positive')
            self.SquidFeedBut.setStyleSheet("color: white; background-color: red")
        else:
            self.SquidFeedStatus = 'NEG'
            self.SquidFeedBut.setText('Negative')
            self.SquidFeedBut.setStyleSheet("color: white; background-color: blue")

    def CurrentButClicked(self):
        if self.CurrentBut.pressed and self.CurrentButStatus == 'I1':
            self.CurrentButStatus = 'I2'
            self.CurrentBut.setText('I2')
            self.CurrentBut.setStyleSheet("color: white; background-color: blue")
        else:
            self.CurrentButStatus = 'I1'
            self.CurrentBut.setText('I1')
            self.CurrentBut.setStyleSheet("color: white; background-color: red")

    def getData(self):
        if self.txtFilePath.endswith('.txt') and os.path.exists(self.txtFilePath) and self.txtFilePath.split('.txt')[0][-1].isnumeric():
            self.data = False
            self.validFile = True
            if '/' in self.txtFilePath:
                self.txtFile = self.txtFilePath.split('/')[-1]
            else:
                self.txtFile = self.txtFilePath.split('\\')[-1]
            self.dat = magnicon_ccc(self.txtFilePath)
            self.bvd = bvd_stat(self.txtFilePath, self.R1Temp, self.R2Temp, self.R1pres, self.R2pres)
            self.setValidData()
            self.data = True 
        else:
            self.setInvalidData()
            
    def setValidData(self):
        self.VMeanLineEdit.setText(str("{:.6e}".format(self.dat.bvdMean)))
        self.VMeanChkLineEdit.setText(str("{:.6e}".format(self.bvd.mean)))
        self.Current1LineEdit.setText(str(self.dat.I1))
        self.FullCycLineEdit.setText(str(self.dat.fullCyc))
        self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))
        self.MeasLineEdit.setText(str("{:2.4f}".format(self.dat.meas)))
        self.DelayLineEdit.setText(str(self.dat.delay))
        self.R1SNLineEdit.setText(self.dat.R1SN)
        self.Current2LineEdit.setText(str(self.dat.I2))
        self.N2LineEdit.setText(str(self.dat.N2))
        self.NAuxLineEdit.setText(str(self.dat.NA))
        self.AppVoltLineEdit.setText(str(self.dat.appVolt))
        self.R2SNLineEdit.setText(self.dat.R2SN)
        self.SHCLineEdit.setText(str(self.dat.SHC))
        self.N1LineEdit.setText(str(self.dat.N1))
        self.CommentsTextBrowser.setText(self.dat.comments)
        self.RelHumLineEdit.setText(str(self.dat.relHum))

        self.R1TempLineEdit.setText(str("{:.4f}".format(self.R1Temp)))
        self.R2TempLineEdit.setText(str("{:.4f}".format(self.R2Temp)))
        self.R1PresLineEdit.setText(str(self.R1pres))
        self.R2PresLineEdit.setText(str(self.R2pres))
        self.updateOilDepth('both')

        self.R1STPLineEdit.setText(str("{:2.7f}".format(self.bvd.R1PPM)))
        self.R2STPLineEdit.setText(str("{:2.7f}".format(self.bvd.R2PPM)))
        self.RampLineEdit.setText(str(self.dat.rampTime))
        self.MeasCycLineEdit.setText(str(int(self.dat.measCyc)))

        self.RatioMeanLineEdit.setText(str("{:.10f}".format(self.bvd.ratioMean)))

        self.StdDevLineEdit.setText(str("{:.6e}".format(self.bvd.std)))
        self.StdDevChkLineEdit.setText(str("{:.6e}".format(self.dat.bvdStd)))
        self.StdDevMeanLineEdit.setText(str("{:.6e}".format(self.bvd.stdMean)))
        self.StdDevMeanChkLineEdit.setText(str("{:.6e}".format(self.dat.stddrt)))

        self.StdDevChkPPMLineEdit.setText(str("{:.7f}".format(self.bvd.stdppm*10**6)))

        self.NLineEdit.setText(str(self.bvd.N))
        self.MeasTimeLineEdit.setText(self.dat.measTimeStamp)
        self.RemTimeLineEdit.setText(self.bvd.remTimeStamp)

        self.MDSSButton.setStyleSheet("color: white; background-color: red")
        self.MDSSButton.setEnabled(True)

        self.bvdCount = []
        self.plotCountCombo.clear()
        for i in range(len(self.bvd.bvdList)):
            self.bvdCount.append(i)
            self.plotCountCombo.addItem(f'Count {i}')

        if len(self.bvd.bvdList) > 400:
            self.bins = int(sqrt(len(self.bvd.bvdList)))
        else:
            self.bins = 20

        self.stdR(self.RButStatus)

    def setInvalidData(self):
        self.validFile = False
        self.VMeanLineEdit.setText("")
        self.VMeanChkLineEdit.setText("")
        self.Current1LineEdit.setText("")
        self.FullCycLineEdit.setText("")
        self.MeasCycLineEdit.setText("")
        self.SampUsedLineEdit.setText("")
        self.RampLineEdit.setText("")
        self.MeasLineEdit.setText("")
        self.DelayLineEdit.setText("")
        self.R1SNLineEdit.setText("")
        self.Current2LineEdit.setText("")
        self.N2LineEdit.setText("")
        self.NAuxLineEdit.setText("")
        self.R2ValueLineEdit.setText("")
        self.AppVoltLineEdit.setText("")
        self.R2SNLineEdit.setText("")
        self.SHCLineEdit.setText("")
        self.N1LineEdit.setText("")
        self.R1ValueLineEdit.setText("")
        self.CommentsTextBrowser.setText("")
        self.RelHumLineEdit.setText("")
        self.R1TotalPresLineEdit.setText("")
        self.R2TotalPresLineEdit.setText("")
        self.R1TempLineEdit.setText("")
        self.R2TempLineEdit.setText("")
        self.R1PresLineEdit.setText("")
        self.R2PresLineEdit.setText("")
        self.R1OilPresLineEdit.setText("")
        self.R2OilPresLineEdit.setText("")
        self.R1STPLineEdit.setText("")
        self.R2STPLineEdit.setText("")
        self.R1PPMLineEdit.setText("")
        self.R2PPMLineEdit.setText("")
        self.RatioMeanLineEdit.setText("")
        self.StdDevLineEdit.setText("")
        self.StdDevMeanLineEdit.setText("")
        self.ppmMeanLineEdit.setText("")
        self.RMeanChkPPMLineEdit.setText("")
        self.StdDevPPMLineEdit.setText("")
        self.StdDevChkPPMLineEdit.setText("")
        self.StdDevMeanPPMLineEdit.setText("")
        self.StdDevChkLineEdit.setText("")
        self.StdDevMeanChkLineEdit.setText("")
        self.C1LineEdit.setText("")
        self.C2LineEdit.setText("")
        self.StdDevC1LineEdit.setText("")
        self.StdDevC2LineEdit.setText("")
        self.C1C2LineEdit.setText("")
        self.NLineEdit.setText("")
        self.MeasTimeLineEdit.setText("")
        self.RemTimeLineEdit.setText("")

        self.MDSSButton.setStyleSheet("")
        self.MDSSButton.setText("No")
        self.MDSSButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.saveStatus = False

        self.SkewnessEdit.setText("")
        self.KurtosisEdit.setText("")

        self.deletedIndex = []
        self.deletedCount = []
        self.deletedBVD = []
        self.bvdCount = []
        self.deletedR1 = []
        self.deletedR2

        self.plotCountCombo.clear()

        if self.plottedBVD or self.plottedAllan or self.plottedSpec:
            self.plottedBVD = False
            self.plottedAllan = False
            self.plottedSpec = False
            self.clearPlots()

    def stdR(self, R: str):
        if R == 'R1':
            self.R1ValueLineEdit.setText(str("{:5.10f}".format(self.bvd.R1)))
            self.R2ValueLineEdit.setText(str("{:5.10f}".format(self.dat.R2NomVal)))
            self.R2PPMLineEdit.setText(str(0))
            self.ppmMeanLineEdit.setText(str("{:.7f}".format(self.bvd.meanR1)))
            self.RMeanChkPPMLineEdit.setText(str("{:.7f}".format(self.bvd.R1MeanChk)))
            self.C1LineEdit.setText(str("{:.7f}".format(self.bvd.C1R1)))
            self.C2LineEdit.setText(str("{:.7f}".format(self.bvd.C2R1)))
            self.C1C2LineEdit.setText(str("{:.7f}".format(self.bvd.C1R1-self.bvd.C2R1)))
            self.StdDevC1LineEdit.setText(str("{:.7f}".format(self.bvd.stdC1R1)))
            self.StdDevC2LineEdit.setText(str("{:.7f}".format(self.bvd.stdC2R1)))
            self.StdDevPPMLineEdit.setText(str("{:.7f}".format(self.bvd.stdR1ppm)))
            self.StdDevMeanPPMLineEdit.setText(str("{:.7f}".format(self.bvd.stdMeanR1)))
            if self.bvd.R1PPM:
                self.R1PPMLineEdit.setText(str("{:2.7f}".format(self.bvd.R1PPM)))
            else:
                self.R1PPMLineEdit.setText(str(0))
        else:
            self.R1ValueLineEdit.setText(str("{:5.10f}".format(self.dat.R1NomVal)))
            self.R2ValueLineEdit.setText(str("{:5.10f}".format(self.bvd.R2)))
            self.R1PPMLineEdit.setText(str(0))
            self.ppmMeanLineEdit.setText(str("{:.7f}".format(self.bvd.meanR2)))
            self.RMeanChkPPMLineEdit.setText(str("{:.7f}".format(self.bvd.R2MeanChk)))
            self.C1LineEdit.setText(str("{:.7f}".format(self.bvd.C1R2)))
            self.C2LineEdit.setText(str("{:.7f}".format(self.bvd.C2R2)))
            self.C1C2LineEdit.setText(str("{:.7f}".format(self.bvd.C1R2-self.bvd.C2R2)))
            self.StdDevC1LineEdit.setText(str("{:.7f}".format(self.bvd.stdC1R2)))
            self.StdDevC2LineEdit.setText(str("{:.7f}".format(self.bvd.stdC2R2)))
            self.StdDevPPMLineEdit.setText(str("{:.7f}".format(self.bvd.stdR2ppm)))
            self.StdDevMeanPPMLineEdit.setText(str("{:.7f}".format(self.bvd.stdMeanR2)))
            if self.bvd.R2PPM:
                self.R2PPMLineEdit.setText(str("{:2.7f}".format(self.bvd.R2PPM)))
            else:
                self.R2PPMLineEdit.setText(str(0))

    def R1PresChanged(self):
        try:
            try:
                self.R1pres = int(self.R1PresLineEdit.text())
                self.getData()
            except ValueError:
                self.R1pres = float(self.R1PresLineEdit.text())
                self.getData()
        except ValueError:
            self.R1PresLineEdit.setText(str(self.R1pres))

    def R2PresChanged(self):
        try:
            try:
                self.R2pres = int(self.R2PresLineEdit.text())
                self.getData()
            except ValueError:
                self.R2pres = float(self.R2PresLineEdit.text())
                self.getData()
        except ValueError:
            self.R2PresLineEdit.setText(str(self.R2pres))

    def oilDepth1Changed(self):
        self.R1OilDepth = self.R1OilDepthSpinBox.value()
        if self.R1PresLineEdit.text():
            self.updateOilDepth('R1')

    def oilDepth2Changed(self):
        self.R2OilDepth = self.R2OilDepthSpinBox.value()
        if self.R2PresLineEdit.text():
            self.updateOilDepth('R2')

    def updateOilDepth(self, R):
        if R == 'R1' or R == 'both':
            self.R1OilPres = 0.8465*9.81*self.R1OilDepth
            self.R1OilPresLineEdit.setText(str("{:.4f}".format(self.R1OilPres)))
            self.R1TotPres = self.R1pres + self.R1OilPres
            self.R1TotalPresLineEdit.setText(str("{:.4f}".format(self.R1TotPres)))
            self.R1OilDepthSpinBox.setValue(self.R1OilDepth)

        if R == 'R2' or R == 'both':
            self.R2OilPres = 0.8465*9.81*self.R2OilDepth
            self.R2OilPresLineEdit.setText(str("{:.4f}".format(self.R2OilPres)))
            self.R2TotPres = self.R2pres + self.R2OilPres
            self.R2TotalPresLineEdit.setText(str("{:.4f}".format(self.R2TotPres)))
            self.R2OilDepthSpinBox.setValue(self.R2OilDepth)

    def temp1Changed(self):
        try:
            self.R1Temp = float(self.R1TempLineEdit.text())
            self.getData()
        except ValueError:
            self.R1TempLineEdit.setText(str("{:.4f}".format(self.R1Temp)))

    def temp2Changed(self):
        try:
            self.R2Temp = float(self.R2TempLineEdit.text())
            self.getData()
        except ValueError:
            self.R2TempLineEdit.setText(str("{:.4f}".format(self.R2Temp)))

    def folderClicked(self):
        self.txtFilePath = filedialog.askopenfilename()
        tkinter.Tk().withdraw()
        self.txtFileLineEdit.setText(self.txtFilePath)
        self.getData()

    def folderEdited(self):
        self.txtFilePath = self.txtFileLineEdit.text()
        self.getData()

    def MDSSClicked(self):
        if self.saveStatus:
            self.saveStatus = False
            self.MDSSButton.setStyleSheet("color: white; background-color: red")
            self.MDSSButton.setText('No')
            self.saveButton.setEnabled(False)
        else:
            self.saveStatus = True
            self.MDSSButton.setStyleSheet("color: white; background-color: green")
            self.MDSSButton.setText('Yes')
            self.saveButton.setEnabled(True)
            self.progressBar.setProperty('value', 0)

    def saveMDSS(self):
        self.progressBar.setProperty('value', 25)
        self.saveStatus = False
        self.MDSSButton.setStyleSheet("color: white; background-color: red")
        self.MDSSButton.setText('No')
        self.saveButton.setEnabled(False)
        self.dat.comments = self.CommentsTextBrowser.toPlainText()
        self.createDataFile()
        self.progressBar.setProperty('value', 100)

    def createDataFile(self):
        writeDataFile(text=self.txtFile, dat_obj=self.dat, bvd_stat_obj=self.bvd, RStatus=self.RButStatus, R1Temp=self.R1Temp,
                      R2Temp=self.R2Temp, R1Pres=self.R1TotPres, R2Pres=self.R2TotPres, I=self.CurrentButStatus, polarity=self.SquidFeedStatus,
                      system=self.MagElecComboBox.currentText(), probe=self.ProbeComboBox.currentText())

    def tabIndexChanged(self):
        if self.tabWidget.currentIndex() == 1 and self.validFile:
            self.plotBVD()
        elif self.tabWidget.currentIndex() == 2 and self.validFile:
            self.plotAllan()
        elif self.tabWidget.currentIndex() == 3 and self.validFile:
            self.plotSpec()

    def deleteBut(self):
        if self.plottedBVD and self.plotCountCombo.count():
            curIndex = self.plotCountCombo.currentIndex()
            self.deletedIndex.append(curIndex)
            self.deletedCount.append(int(self.plotCountCombo.currentText().replace('Count ', '')))
            self.deletedBVD.append(self.bvd.bvdList[curIndex])
            self.plotCountCombo.removeItem(curIndex)
            self.bvd.bvdList.pop(curIndex)
            self.bvdCount.pop(curIndex)

            self.deletedR1.append(self.bvd.R1List[curIndex])
            self.deletedR2.append(self.bvd.R2List[curIndex])
            self.bvd.R1List.pop(curIndex)
            self.bvd.R2List.pop(curIndex)
            self.plotBVD()

    def restoreDeleted(self, loop=None):
        if self.deletedCount:
            self.plotCountCombo.insertItem(self.deletedIndex[-1], f'Count {self.deletedCount[-1]}')
            self.bvdCount.insert(self.deletedIndex[-1], self.deletedCount[-1])
            self.bvd.bvdList.insert(self.deletedIndex[-1], self.deletedBVD[-1])
            self.bvd.R1List.insert(self.deletedIndex[-1], self.deletedR1[-1])
            self.bvd.R2List.insert(self.deletedIndex[-1], self.deletedR2[-1])
            self.deletedIndex.pop(-1)
            self.deletedCount.pop(-1)
            self.deletedBVD.pop(-1)
            self.deletedR1.pop(-1)
            self.deletedR2.pop(-1)
            if loop is None:
                self.plotBVD()

    def replotAll(self):
        looped = False
        while(self.deletedCount):
            self.restoreDeleted(loop=True)
            looped = True
        if looped:
            self.plotBVD()

def is_overlapping(overlapping: str) -> bool:
    if overlapping == 'overlapping':
        return True
    else:
        return False

def main():
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()