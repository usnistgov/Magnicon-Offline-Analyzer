import sys, os
from numpy import linspace, array

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QRect, QMetaObject, QCoreApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, \
                             QLabel, QPushButton, QComboBox, QTextBrowser, QTabWidget, \
                             QSpacerItem, QGridLayout, QLineEdit, QFrame, QSizePolicy, \
                             QMenuBar, QSpinBox, QProgressBar, QToolButton, QStatusBar, \
                             QTextEdit, QFileDialog)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import MaxNLocator, ScalarFormatter, StrMethodFormatter
from numpy import sqrt, std, mean, ones

# custom imports
from bvd_stats import bvd_stat
from skew_and_kurt import skewness, kurtosis
from magnicon_ccc import magnicon_ccc
from create_mag_ccc_datafile import writeDataFile
import mystat

# python globals
__version__ = '0.2' # Program version string
red_style   = "color: white; background-color: red"
blue_style  = "color: white; background-color: blue"
green_style = "color: white; background-color: green"
winSizeH = 1000
winSizeV = 840

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

class aboutWindow(QWidget):
    def __init__(self):
        """QWidget class for showing the About window to display general program
           information 
        """
        super().__init__()
        self.setWindowTitle("About")
        self.setFixedSize(300, 200)
        self.te_about = QTextEdit()
        self.te_about.setReadOnly(True)
        self.te_about.setPlainText("Data Analysis software for the powerful Magnicon")
        self.te_about.append("CCC probe and electronics")
        self.te_about.append("Developers: Andrew Geckle & Alireza Panna")
        self.te_about.append("Maintainers: Alireza Panna")
        self.te_about.append("Email: alireza.panna@nist.gov")
        layout = QVBoxLayout()
        layout.addWidget(self.te_about)
        self.setLayout(layout)

class Ui_mainWindow(object):

    def setupUi(self, mainWindow) -> None:
        global winSizeH, winSizeV
        mainWindow.setFixedSize(winSizeH, winSizeV)
        mainWindow.setWindowIcon(QIcon(base_dir + '\\icons\\analyzer.ico'))
        self.initializations()

        self.centralwidget = QWidget(parent=mainWindow)
        self.tabWidget = QTabWidget(parent=self.centralwidget)
        self.tabWidget.setGeometry(QRect(0, 0, winSizeH - 125, winSizeV))
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
        # options and actions for the top window menu
        self.file_action = QAction("&Open...")
        self.file_action.setStatusTip("Open data file")
        self.file_action.setShortcut("Ctrl + O")
        self.file_action.triggered.connect(self.folderClicked)

        self.close_action = QAction("&Quit")
        self.close_action.setStatusTip("Quit this program")
        self.close_action.setShortcut("Ctrl + Q")
        self.close_action.triggered.connect(self.quit)

        self.about_action = QAction("&About")
        self.about_action.setStatusTip("Program information & license")
        self.about_action.triggered.connect(self._about)

        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(parent=mainWindow)
        self.menubar.setGeometry(QRect(0, 0, winSizeH, 22))
        self._create_menubar()
        mainWindow.setMenuBar(self.menubar)
        
        self.dialog = QFileDialog(parent=mainWindow)
        # self.dialog.setFileMode(QFileDialog.AnyFile)

        self.statusbar = QStatusBar(parent=mainWindow)
        mainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(mainWindow)
        self.tabWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(mainWindow)

    def _create_menubar(self, ):
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(self.file_action)
        self.file_menu.addAction(self.close_action)
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(self.about_action)

    def _about(self,):
        self.about_window = aboutWindow()
        self.about_window.show()
        return

    def quit(self,):
        QtCore.QCoreApplication.instance().quit
        app.quit()
        return

    def initializations(self) -> None:
        self.txtFilePath  = ''
        self.validFile    = False
        self.data         = False
        self.plottedBVD   = False
        self.plottedAllan = False
        self.plottedSpec  = False

        self.R1Temp     = 25.0000
        self.R2Temp     = 25.0000
        self.R1pres     = 101325
        self.R2pres     = 101325
        self.R1OilDepth = 203
        self.R2OilDepth = 203
        self.alpha      = 0.25
        self.R1OilPres  = 0.8465*9.81*self.R1OilDepth
        self.R2OilPres  = 0.8465*9.81*self.R2OilDepth
        self.R1TotPres  = self.R1pres + self.R1OilPres
        self.R2TotPres  = self.R2pres + self.R2OilPres

        self.RButStatus       = 'R1'
        self.SquidFeedStatus  = 'NEG'
        self.CurrentButStatus = 'I1'
        self.saveStatus       = False

        self.bvdCount     = []
        self.deletedIndex = []
        self.deletedCount = []
        self.deletedBVD   = []
        self.deletedR1    = []
        self.deletedR2    = []
        self.bvd = None
        
        self.lbl_width = 110
        self.lbl_height = 25
        self.col0x = 20
        self.col1x = 140
        self.col2x = 260
        self.col3x = 380
        self.col4x = 520
        self.col5x = 640
        self.col6x = 760
        self.col7x = 880
        self.coly = 60

    # Set up for the labels
    def setLabels(self) -> None:
        # col0
        self.R1SNLabel = QLabel(parent=self.SetResTab)
        self.R1SNLabel.setGeometry(QRect(self.col0x, 30, self.lbl_width, self.lbl_height))
        self.R2SNLabel = QLabel(parent=self.SetResTab)
        self.R2SNLabel.setGeometry(QRect(self.col0x, 90, self.lbl_width, self.lbl_height))
        self.AppVoltLabel = QLabel(parent=self.SetResTab)
        self.AppVoltLabel.setGeometry(QRect(self.col0x, 150, self.lbl_width, self.lbl_height))
        self.N1Label = QLabel(parent=self.SetResTab)
        self.N1Label.setGeometry(QRect(self.col0x, 210, self.lbl_width, self.lbl_height))
        self.MeasCycLabel = QLabel(parent=self.SetResTab)
        self.MeasCycLabel.setGeometry(QRect(self.col0x, 270, self.lbl_width, self.lbl_height))
        self.FullCycLabel = QLabel(parent=self.SetResTab)
        self.FullCycLabel.setGeometry(QRect(self.col0x, 330, self.lbl_width, self.lbl_height))
        self.R1PresLabel = QLabel(parent=self.SetResTab)
        self.R1PresLabel.setGeometry(QRect(self.col0x, 390, self.lbl_width, self.lbl_height))
        self.R2PresLabel = QLabel(parent=self.SetResTab)
        self.R2PresLabel.setGeometry(QRect(self.col0x, 450, self.lbl_width, self.lbl_height))
        self.CommentsLabel = QLabel(parent=self.SetResTab)
        self.CommentsLabel.setGeometry(QRect(self.col0x, 510, self.lbl_width, self.lbl_height))
        self.txtFileLabel = QLabel(parent=self.SetResTab)
        self.txtFileLabel.setGeometry(QRect(self.col0x, 600, self.lbl_width, self.lbl_height))
        self.MagElecLabel = QLabel(parent=self.SetResTab)
        self.MagElecLabel.setGeometry(QRect(self.col0x, 630, self.lbl_width, self.lbl_height))
        self.ProbeLabel = QLabel(parent=self.SetResTab)
        self.ProbeLabel.setGeometry(QRect(self.col0x, 690, self.lbl_width, self.lbl_height))
        # col1
        self.R1PPMLabel = QLabel(parent=self.SetResTab)
        self.R1PPMLabel.setGeometry(QRect(self.col1x, 30, self.lbl_width, self.lbl_height))
        self.R2PPMLabel = QLabel(parent=self.SetResTab)
        self.R2PPMLabel.setGeometry(QRect(self.col1x, 90, self.lbl_width, self.lbl_height))
        self.Current1Label = QLabel(parent=self.SetResTab)
        self.Current1Label.setGeometry(QRect(self.col1x, 150, self.lbl_width, self.lbl_height))
        self.N2Label = QLabel(parent=self.SetResTab)
        self.N2Label.setGeometry(QRect(self.col1x, 210, self.lbl_width, self.lbl_height))
        self.SHCLabel = QLabel(parent=self.SetResTab)
        self.SHCLabel.setGeometry(QRect(self.col1x, 270, self.lbl_width, self.lbl_height))
        self.RampLabel = QLabel(parent=self.SetResTab)
        self.RampLabel.setGeometry(QRect(self.col1x, 330, self.lbl_width, self.lbl_height))
        self.R1OilDepthLabel = QLabel(parent=self.SetResTab)
        self.R1OilDepthLabel.setGeometry(QRect(self.col1x, 390, self.lbl_width, self.lbl_height))
        self.R2OilDepthLabel = QLabel(parent=self.SetResTab)
        self.R2OilDepthLabel.setGeometry(QRect(self.col1x, 450, self.lbl_width, self.lbl_height))
        # col2
        self.R1ValueLabel = QLabel(parent=self.SetResTab)
        self.R1ValueLabel.setGeometry(QRect(self.col2x, 30, self.lbl_width, self.lbl_height))
        self.R2ValueLabel = QLabel(parent=self.SetResTab)
        self.R2ValueLabel.setGeometry(QRect(self.col2x, 90, self.lbl_width, self.lbl_height))
        self.Current2Label = QLabel(parent=self.SetResTab)
        self.Current2Label.setGeometry(QRect(self.col2x, 150, self.lbl_width, self.lbl_height))
        self.NAuxLabel = QLabel(parent=self.SetResTab)
        self.NAuxLabel.setGeometry(QRect(self.col2x, 210, self.lbl_width, self.lbl_height))
        self.SampUsedLabel = QLabel(parent=self.SetResTab)
        self.SampUsedLabel.setGeometry(QRect(self.col2x, 270, self.lbl_width, self.lbl_height))
        self.MeasLabel = QLabel(parent=self.SetResTab)
        self.MeasLabel.setGeometry(QRect(self.col2x, 330, self.lbl_width, self.lbl_height))
        self.R1OilPresLabel = QLabel(parent=self.SetResTab)
        self.R1OilPresLabel.setGeometry(QRect(self.col2x, 390, self.lbl_width, self.lbl_height))
        self.R2OilPresLabel = QLabel(parent=self.SetResTab)
        self.R2OilPresLabel.setGeometry(QRect(self.col2x, 450, self.lbl_width, self.lbl_height))
        # col3
        self.ReadingDelayLabel = QLabel(parent=self.SetResTab)
        self.ReadingDelayLabel.setGeometry(QRect(self.col3x, 30, self.lbl_width, self.lbl_height))
        self.MeasTimeLabel = QLabel(parent=self.SetResTab)
        self.MeasTimeLabel.setGeometry(QRect(self.col3x, 90, self.lbl_width, self.lbl_height))
        self.RemTimeLabel = QLabel(parent=self.SetResTab)
        self.RemTimeLabel.setGeometry(QRect(self.col3x, 150, self.lbl_width, self.lbl_height))
        self.R1TotalPresLabel = QLabel(parent=self.SetResTab)
        self.R1TotalPresLabel.setGeometry(QRect(self.col3x, 210, self.lbl_width, self.lbl_height))
        self.R2TotalPresLabel = QLabel(parent=self.SetResTab)
        self.R2TotalPresLabel.setGeometry(QRect(self.col3x, 270, self.lbl_width, self.lbl_height))
        self.R1TempLabel = QLabel(parent=self.SetResTab)
        self.R1TempLabel.setGeometry(QRect(self.col3x, 330, self.lbl_width, self.lbl_height))
        self.R2TempLabel = QLabel(parent=self.SetResTab)
        self.R2TempLabel.setGeometry(QRect(self.col3x, 390, self.lbl_width, self.lbl_height))
        self.RelHumLabel = QLabel(parent=self.SetResTab)
        self.RelHumLabel.setGeometry(QRect(self.col3x, 450, self.lbl_width, self.lbl_height))
        self.SquidFeedLabel = QLabel(parent=self.SetResTab)
        self.SquidFeedLabel.setGeometry(QRect(self.col3x, 630, self.lbl_width, self.lbl_height))
        self.CurrentButLabel = QLabel(parent=self.SetResTab)
        self.CurrentButLabel.setGeometry(QRect(self.col3x, 690, self.lbl_width, self.lbl_height))
        # col4
        self.VMeanLabel = QLabel(parent=self.SetResTab)
        self.VMeanLabel.setGeometry(QRect(self.col4x, 30, self.lbl_width, self.lbl_height))
        self.StdDevLabel = QLabel(parent=self.SetResTab)
        self.StdDevLabel.setGeometry(QRect(self.col4x, 90, self.lbl_width, self.lbl_height))
        self.StdDevMeanLabel = QLabel(parent=self.SetResTab)
        self.StdDevMeanLabel.setGeometry(QRect(self.col4x, 150, self.lbl_width, self.lbl_height))
        self.C1Label = QLabel(parent=self.SetResTab)
        self.C1Label.setGeometry(QRect(self.col4x, 210, self.lbl_width, self.lbl_height))
        self.C2Label = QLabel(parent=self.SetResTab)
        self.C2Label.setGeometry(QRect(self.col4x, 270, self.lbl_width, self.lbl_height))
        # col5
        self.VMeanChkLabel = QLabel(parent=self.SetResTab)
        self.VMeanChkLabel.setGeometry(QRect(self.col5x, 30, self.lbl_width, self.lbl_height))
        self.StdDevChkLabel = QLabel(parent=self.SetResTab)
        self.StdDevChkLabel.setGeometry(QRect(self.col5x, 90, self.lbl_width, self.lbl_height))
        self.StdDevMeanChkLabel = QLabel(parent=self.SetResTab)
        self.StdDevMeanChkLabel.setGeometry(QRect(self.col5x, 150, self.lbl_width, self.lbl_height))
        self.StdDevC1Label = QLabel(parent=self.SetResTab)
        self.StdDevC1Label.setGeometry(QRect(self.col5x, 210, self.lbl_width, self.lbl_height))
        self.StdDevC2Label = QLabel(parent=self.SetResTab)
        self.StdDevC2Label.setGeometry(QRect(self.col5x, 270, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLabel = QLabel(parent=self.SetResTab)
        self.RMeanChkPPMLabel.setGeometry(QRect(self.col5x, 330, self.lbl_width, self.lbl_height))
        # col6
        self.R1STPLabel = QLabel(parent=self.SetResTab)
        self.R1STPLabel.setGeometry(QRect(self.col6x, 90, self.lbl_width, self.lbl_height))
        self.R2STPLabel = QLabel(parent=self.SetResTab)
        self.R2STPLabel.setGeometry(QRect(self.col6x, 30, self.lbl_width, self.lbl_height))
        self.NLabel = QLabel(parent=self.SetResTab)
        self.NLabel.setGeometry(QRect(self.col6x, 150, self.lbl_width, self.lbl_height))
        self.RatioMeanLabel = QLabel(parent=self.SetResTab)
        self.RatioMeanLabel.setGeometry(QRect(self.col6x, 210,self.lbl_width, self.lbl_height))
        self.StdDevPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevPPMLabel.setGeometry(QRect(self.col6x, 270, self.lbl_width, self.lbl_height))
        self.StdDevChkPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevChkPPMLabel.setGeometry(QRect(self.col6x, 330, self.lbl_width, self.lbl_height))
        # col7
        self.StandardRLabel = QLabel(parent=self.centralwidget)
        self.StandardRLabel.setGeometry(QRect(self.col7x, 30, self.lbl_width, self.lbl_height))
        self.MDSSLabel = QLabel(parent=self.centralwidget)
        self.MDSSLabel.setGeometry(QRect(self.col7x, 90, self.lbl_width, self.lbl_height))
        self.ppmMeanLabel = QLabel(parent=self.centralwidget)
        self.ppmMeanLabel.setGeometry(QRect(self.col7x, 270, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLabel = QLabel(parent=self.centralwidget)
        self.StdDevMeanPPMLabel.setGeometry(QRect(self.col7x, 330, self.lbl_width, self.lbl_height))
        self.C1C2Label = QLabel(parent=self.centralwidget)
        self.C1C2Label.setGeometry(QRect(self.col7x, 390, self.lbl_width, self.lbl_height))

        self.ResultsLabel = QLabel(parent=self.SetResTab)
        self.ResultsLabel.setGeometry(QRect(700, 10, self.lbl_width, self.lbl_height))
        self.SettingsLabel = QLabel(parent=self.SetResTab)
        self.SettingsLabel.setGeometry(QRect(220, 10, self.lbl_width, self.lbl_height))
    # Set up the read only LineEdits
    def setLineEdits(self) -> None:
        # col0
        self.R1SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1SNLineEdit.setGeometry(QRect(self.col0x, self.coly, self.lbl_width, self.lbl_height))
        self.R1SNLineEdit.setReadOnly(True)
        self.R2SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2SNLineEdit.setGeometry(QRect(self.col0x, self.coly*2 , self.lbl_width, self.lbl_height))
        self.R2SNLineEdit.setReadOnly(True)
        self.AppVoltLineEdit = QLineEdit(parent=self.SetResTab)
        self.AppVoltLineEdit.setGeometry(QRect(self.col0x, self.coly*3, self.lbl_width, self.lbl_height))
        self.AppVoltLineEdit.setReadOnly(True)
        self.N1LineEdit = QLineEdit(parent=self.SetResTab)
        self.N1LineEdit.setGeometry(QRect(self.col0x, self.coly*4, self.lbl_width, self.lbl_height))
        self.N1LineEdit.setReadOnly(True)
        self.MeasCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasCycLineEdit.setGeometry(QRect(self.col0x, self.coly*5, self.lbl_width, self.lbl_height))
        self.MeasCycLineEdit.setReadOnly(True)
        self.FullCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.FullCycLineEdit.setGeometry(QRect(self.col0x, self.coly*6, self.lbl_width, self.lbl_height))
        self.FullCycLineEdit.setReadOnly(True)
        self.R1PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1PresLineEdit.setGeometry(QRect(self.col0x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1PresLineEdit.returnPressed.connect(self.R1PresChanged)
        self.R2PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PresLineEdit.setGeometry(QRect(self.col0x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2PresLineEdit.returnPressed.connect(self.R2PresChanged)
        self.txtFileLineEdit = QLineEdit(parent=self.SetResTab)
        self.txtFileLineEdit.setGeometry(QRect(self.col0x, self.coly*10, int(self.lbl_width*3.2), self.lbl_height))
        self.txtFileLineEdit.returnPressed.connect(self.folderEdited)
        # col1
        self.R1PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1PPMLineEdit.setGeometry(QRect(self.col1x, self.coly, self.lbl_width, self.lbl_height))
        self.R1PPMLineEdit.setReadOnly(True)
        self.R2PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PPMLineEdit.setGeometry(QRect(self.col1x, self.coly*2, self.lbl_width, self.lbl_height))
        self.R2PPMLineEdit.setReadOnly(True)
        self.Current1LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current1LineEdit.setGeometry(QRect(self.col1x, self.coly*3, self.lbl_width, self.lbl_height))
        self.Current1LineEdit.setReadOnly(True)
        self.N2LineEdit = QLineEdit(parent=self.SetResTab)
        self.N2LineEdit.setGeometry(QRect(self.col1x, self.coly*4, self.lbl_width, self.lbl_height))
        self.N2LineEdit.setReadOnly(True)
        self.SHCLineEdit = QLineEdit(parent=self.SetResTab)
        self.SHCLineEdit.setGeometry(QRect(self.col1x, self.coly*5, self.lbl_width, self.lbl_height))
        self.SHCLineEdit.setReadOnly(True)
        self.RampLineEdit = QLineEdit(parent=self.SetResTab)
        self.RampLineEdit.setGeometry(QRect(self.col1x, self.coly*6, self.lbl_width, self.lbl_height))
        self.RampLineEdit.setReadOnly(True)
        # col2
        self.R1ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1ValueLineEdit.setGeometry(QRect(self.col2x, self.coly, self.lbl_width, self.lbl_height))
        self.R1ValueLineEdit.setReadOnly(True)
        self.R2ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2ValueLineEdit.setGeometry(QRect(self.col2x, self.coly*2, self.lbl_width, self.lbl_height))
        self.R2ValueLineEdit.setReadOnly(True)
        self.Current2LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current2LineEdit.setGeometry(QRect(self.col2x, self.coly*3, self.lbl_width, self.lbl_height))
        self.Current2LineEdit.setReadOnly(True)
        self.NAuxLineEdit = QLineEdit(parent=self.SetResTab)
        self.NAuxLineEdit.setGeometry(QRect(self.col2x, self.coly*4, self.lbl_width, self.lbl_height))
        self.NAuxLineEdit.setReadOnly(True)
        self.SampUsedLineEdit = QLineEdit(parent=self.SetResTab)
        self.SampUsedLineEdit.setGeometry(QRect(self.col2x, self.coly*5, self.lbl_width, self.lbl_height))
        self.SampUsedLineEdit.setReadOnly(True)
        self.MeasLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasLineEdit.setGeometry(QRect(self.col2x, self.coly*6, self.lbl_width, self.lbl_height))
        self.MeasLineEdit.setReadOnly(True)
        self.R1OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1OilPresLineEdit.setGeometry(QRect(self.col2x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1OilPresLineEdit.setReadOnly(True)
        self.R2OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2OilPresLineEdit.setGeometry(QRect(self.col2x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2OilPresLineEdit.setReadOnly(True)
        # col3
        self.MeasTimeLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasTimeLineEdit.setGeometry(QRect(self.col3x, self.coly*2, self.lbl_width, self.lbl_height))
        self.MeasTimeLineEdit.setReadOnly(True)
        self.RemTimeLineEdit = QLineEdit(parent=self.SetResTab)
        self.RemTimeLineEdit.setGeometry(QRect(self.col3x, self.coly*3, self.lbl_width, self.lbl_height))
        self.RemTimeLineEdit.setReadOnly(True)
        self.R1TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TotalPresLineEdit.setGeometry(QRect(self.col3x, self.coly*4, self.lbl_width, self.lbl_height))
        self.R1TotalPresLineEdit.setReadOnly(True)
        self.R2TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TotalPresLineEdit.setGeometry(QRect(self.col3x, self.coly*5, self.lbl_width, self.lbl_height))
        self.R2TotalPresLineEdit.setReadOnly(True)
        self.R1TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TempLineEdit.setGeometry(QRect(self.col3x, self.coly*6, self.lbl_width, self.lbl_height))
        self.R1TempLineEdit.returnPressed.connect(self.temp1Changed)
        self.R2TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TempLineEdit.setGeometry(QRect(self.col3x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R2TempLineEdit.returnPressed.connect(self.temp2Changed)
        self.RelHumLineEdit = QLineEdit(parent=self.SetResTab)
        self.RelHumLineEdit.setGeometry(QRect(self.col3x, self.coly*8, self.lbl_width, self.lbl_height))
        # col4
        self.VMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanLineEdit.setGeometry(QRect(self.col4x, self.coly, self.lbl_width, self.lbl_height))
        self.VMeanLineEdit.setReadOnly(True)
        self.StdDevLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevLineEdit.setGeometry(QRect(self.col4x, self.coly*2, self.lbl_width, self.lbl_height))
        self.StdDevLineEdit.setReadOnly(True)
        self.StdDevMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanLineEdit.setGeometry(QRect(self.col4x, self.coly*3, self.lbl_width, self.lbl_height))
        self.StdDevMeanLineEdit.setReadOnly(True)
        self.C1LineEdit = QLineEdit(parent=self.SetResTab)
        self.C1LineEdit.setGeometry(QRect(self.col4x, self.coly*4, self.lbl_width, self.lbl_height))
        self.C1LineEdit.setStyleSheet("")
        self.C1LineEdit.setReadOnly(True)
        self.C2LineEdit = QLineEdit(parent=self.SetResTab)
        self.C2LineEdit.setGeometry(QRect(self.col4x, self.coly*5, self.lbl_width, self.lbl_height))
        self.C2LineEdit.setStyleSheet("")
        self.C2LineEdit.setReadOnly(True)
        # col5
        self.VMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanChkLineEdit.setGeometry(QRect(self.col5x, self.coly, self.lbl_width, self.lbl_height))
        self.VMeanChkLineEdit.setReadOnly(True)
        self.StdDevChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkLineEdit.setGeometry(QRect(self.col5x, self.coly*2, self.lbl_width, self.lbl_height))
        self.StdDevChkLineEdit.setReadOnly(True)
        self.StdDevMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanChkLineEdit.setGeometry(QRect(self.col5x, self.coly*3, self.lbl_width, self.lbl_height))
        self.StdDevMeanChkLineEdit.setReadOnly(True)
        self.StdDevC1LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC1LineEdit.setGeometry(QRect(self.col5x, self.coly*4, self.lbl_width, self.lbl_height))
        self.StdDevC1LineEdit.setStyleSheet("")
        self.StdDevC1LineEdit.setReadOnly(True)
        self.StdDevC2LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC2LineEdit.setGeometry(QRect(self.col5x, self.coly*5, self.lbl_width, self.lbl_height))
        self.StdDevC2LineEdit.setStyleSheet("")
        self.StdDevC2LineEdit.setReadOnly(True)
        self.RMeanChkPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.RMeanChkPPMLineEdit.setGeometry(QRect(self.col5x, self.coly*6, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLineEdit.setStyleSheet("")
        self.RMeanChkPPMLineEdit.setReadOnly(True)
        # col6
        self.R1STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1STPLineEdit.setGeometry(QRect(self.col6x, self.coly, self.lbl_width - 5, self.lbl_height))
        self.R1STPLineEdit.setReadOnly(True)
        self.R2STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2STPLineEdit.setGeometry(QRect(self.col6x, self.coly*2, self.lbl_width - 5, self.lbl_height))
        self.R2STPLineEdit.setReadOnly(True)
        self.NLineEdit = QLineEdit(parent=self.SetResTab)
        self.NLineEdit.setGeometry(QRect(self.col6x, self.coly*3, self.lbl_width- 5, self.lbl_height))
        self.NLineEdit.setReadOnly(True)
        self.RatioMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.RatioMeanLineEdit.setGeometry(QRect(self.col6x, self.coly*4, self.lbl_width - 5, self.lbl_height))
        self.RatioMeanLineEdit.setStyleSheet("")
        self.RatioMeanLineEdit.setReadOnly(True)
        self.StdDevPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevPPMLineEdit.setGeometry(QRect(self.col6x, self.coly*5, self.lbl_width - 5, self.lbl_height))
        self.StdDevPPMLineEdit.setStyleSheet("")
        self.StdDevPPMLineEdit.setReadOnly(True)
        self.StdDevChkPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkPPMLineEdit.setGeometry(QRect(self.col6x, self.coly*6, self.lbl_width - 5, self.lbl_height))
        self.StdDevChkPPMLineEdit.setStyleSheet("")
        self.StdDevChkPPMLineEdit.setReadOnly(True)
        # col7
        self.ppmMeanLineEdit = QLineEdit(parent=self.centralwidget)
        self.ppmMeanLineEdit.setGeometry(QRect(self.col7x, self.coly*5, self.lbl_width, self.lbl_height))
        self.ppmMeanLineEdit.setStyleSheet("")
        self.ppmMeanLineEdit.setReadOnly(True)
        self.StdDevMeanPPMLineEdit = QLineEdit(parent=self.centralwidget)
        self.StdDevMeanPPMLineEdit.setGeometry(QRect(self.col7x, self.coly*6, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLineEdit.setStyleSheet("")
        self.StdDevMeanPPMLineEdit.setReadOnly(True)
        self.C1C2LineEdit = QLineEdit(parent=self.centralwidget)
        self.C1C2LineEdit.setGeometry(QRect(self.col7x, self.coly*7, self.lbl_width, self.lbl_height))
        self.C1C2LineEdit.setStyleSheet("")
        self.C1C2LineEdit.setReadOnly(True)

    def BVDTabSetUp(self) -> None:
        global winSizeH
        self.BVDTab = QWidget()
        self.tabWidget.addTab(self.BVDTab, "")
        self.BVDVerticalLayoutWidget = QWidget(parent=self.BVDTab)
        self.BVDVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH-125, 691))
        self.BVDVerticalLayout = QVBoxLayout(self.BVDVerticalLayoutWidget)
        # self.fig = plt.figure(figsize=(1,1),dpi=100)
        self.BVDfig = plt.figure()
        self.BVDax1 = self.BVDfig.add_subplot(2, 3, (1, 3))
        self.BVDax2 = self.BVDfig.add_subplot(2, 3, (4, 5))
        self.BVDax3 = self.BVDfig.add_subplot(2, 3, 6)
        # self.BVDax1 = self.BVDfig.add_subplot(2, 100, (1, 100))
        # self.BVDax2 = self.BVDfig.add_subplot(2, 100, (101, 175))
        # self.BVDax3 = self.BVDfig.add_subplot(2, 100, (176, 200))
        self.BVDfig.set_tight_layout(True)
        # self.BVDfig.subplots_adjust(wspace=0, hspace=0)
        self.BVDax1.tick_params(which='both', direction='in')
        self.BVDax2.tick_params(which='both', direction='in')
        self.BVDax3.tick_params(which='both', direction='in')
        self.BVDcanvas = FigureCanvas(self.BVDfig)
        self.BVDVerticalLayout.addWidget(NavigationToolbar(self.BVDcanvas))
        self.BVDVerticalLayout.addWidget(self.BVDcanvas)
        gridWidget = QWidget(self.BVDTab)
        gridWidget.setGeometry(QRect(0, 690, winSizeH-125, 81))
        grid = QGridLayout(gridWidget)
        grid.setSpacing(5)
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

        SkewnessLabel = QLabel('Skewness', parent=gridWidget)
        KurtosisLabel = QLabel('Kurtosis', parent=gridWidget)
        self.SkewnessEdit = QLineEdit(gridWidget)
        self.SkewnessEdit.setReadOnly(True)
        self.KurtosisEdit = QLineEdit(gridWidget)
        self.KurtosisEdit.setReadOnly(True)
        Spacer1 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        Spacer2 = QSpacerItem(600, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
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

    def AllanTabSetUp(self) -> None:
        """Set up the tab widget for showing allan deviation plots
        Returns
        -------
        None.
        """
        self.AllanTab = QWidget()
        self.tabWidget.addTab(self.AllanTab, "")
        self.AllanVerticalLayoutWidget = QWidget(parent=self.AllanTab)
        self.AllanVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH-125, 761))
        self.AllanVerticalLayout = QVBoxLayout(self.AllanVerticalLayoutWidget)
        self.Allanfig = plt.figure()
        self.Allanax1 = self.Allanfig.add_subplot(2,2,1)
        self.Allanax2 = self.Allanfig.add_subplot(2,2,2)
        self.Allanax3 = self.Allanfig.add_subplot(2,2,3)
        self.Allanax4 = self.Allanfig.add_subplot(2,2,4)
        self.Allanax1.tick_params(axis='both', which='both', direction='in')
        self.Allanax2.tick_params(axis='both', which='both', direction='in')
        self.Allanax3.tick_params(axis='both', which='both', direction='in')
        self.Allanax4.tick_params(axis='both', which='both', direction='in')
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

    def SpecTabSetUp(self) -> None:
        global winSizeH
        self.SpecTab = QWidget()
        self.tabWidget.addTab(self.SpecTab, "")
        self.SpecVerticalLayoutWidget = QWidget(parent=self.SpecTab)
        self.SpecVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH - 125, 761))
        self.SpecVerticalLayout = QVBoxLayout(self.SpecVerticalLayoutWidget)

        self.Specfig = plt.figure()
        self.SpecAx = self.Specfig.add_subplot(2,1,1)
        self.SpecAx.tick_params(direction='in')
        self.PowerSpecAx = self.Specfig.add_subplot(2,1,2)
        self.PowerSpecAx.tick_params(direction='in')
        self.SpecCanvas = FigureCanvas(self.Specfig)
        self.SpecVerticalLayout.addWidget(NavigationToolbar(self.SpecCanvas))
        self.SpecVerticalLayout.addWidget(self.SpecCanvas)

    def setButtons(self) -> None:
        self.folderToolButton = QToolButton(parent=self.SetResTab)
        self.folderToolButton.setGeometry(QRect(self.col3x, self.coly*10, 40, self.lbl_height))
        self.folderToolButton.setIcon(QIcon(base_dir + r'\icons\folder.ico'))
        self.folderToolButton.clicked.connect(self.folderClicked)
        self.SquidFeedBut = QPushButton(parent=self.SetResTab)
        self.SquidFeedBut.setGeometry(QRect(self.col3x, self.coly*11, self.lbl_width, int(self.lbl_height*1.2)))
        self.SquidFeedBut.setStyleSheet(blue_style)
        self.SquidFeedBut.clicked.connect(self.SquidButClicked)
        self.CurrentBut = QPushButton(parent=self.SetResTab)
        self.CurrentBut.setGeometry(QRect(self.col3x, self.coly*12, self.lbl_width, int(self.lbl_height*1.2)))
        self.CurrentBut.setStyleSheet(red_style)
        self.CurrentBut.clicked.connect(self.CurrentButClicked)
        self.StandardRBut = QPushButton(parent=self.centralwidget)
        self.StandardRBut.setGeometry(QRect(self.col7x, self.coly, self.lbl_width - 10, int(self.lbl_height*1.2)))
        self.StandardRBut.setStyleSheet(red_style)
        self.StandardRBut.clicked.connect(self.RButClicked)
        self.MDSSButton = QPushButton(parent=self.centralwidget)
        self.MDSSButton.setGeometry(QRect(self.col7x, self.coly*2, self.lbl_width - 10, int(self.lbl_height*1.2)))
        # self.MDSSButton.setStyleSheet("color: white; background-color: red")
        self.MDSSButton.setEnabled(False)
        self.MDSSButton.clicked.connect(self.MDSSClicked)

        self.saveButton = QPushButton(parent=self.centralwidget)
        self.saveButton.setGeometry(QRect(self.col7x, self.coly*3, self.lbl_width - 10, int(self.lbl_height*1.2)))
        self.saveButton.setEnabled(False)
        self.saveButton.clicked.connect(self.saveMDSS)

    def setSpinBoxes(self) -> None:
        self.R1OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R1OilDepthSpinBox.setGeometry(QRect(self.col1x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1OilDepthSpinBox.setMaximum(1000)
        self.R1OilDepthSpinBox.valueChanged.connect(self.oilDepth1Changed)
        self.R2OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R2OilDepthSpinBox.setGeometry(QRect(self.col1x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2OilDepthSpinBox.setMaximum(1000)
        self.R2OilDepthSpinBox.valueChanged.connect(self.oilDepth2Changed)

        self.ReadingDelaySpinBox = QSpinBox(parent=self.SetResTab)
        self.ReadingDelaySpinBox.setGeometry(QRect(self.col3x, self.coly, self.lbl_width, self.lbl_height))

    def setComboBoxes(self) -> None:
        self.MagElecComboBox = QComboBox(parent=self.SetResTab)
        self.MagElecComboBox.setGeometry(QRect(self.col0x, self.coly*11, self.lbl_width, self.lbl_height))
        self.MagElecComboBox.setEditable(False)
        self.MagElecComboBox.addItem('CCC2014-01')
        self.MagElecComboBox.addItem('CCC2019-01')

        self.ProbeComboBox = QComboBox(parent=self.SetResTab)
        self.ProbeComboBox.setGeometry(QRect(self.col0x, self.coly*12, self.lbl_width, self.lbl_height))
        self.ProbeComboBox.setEditable(False)
        self.ProbeComboBox.addItem('Magnicon1')
        self.ProbeComboBox.addItem('NIST1')

    def setMisc(self) -> None:
        self.SetResDivider = QFrame(parent=self.SetResTab)
        self.SetResDivider.setGeometry(QRect(self.col3x + self.lbl_width + 10, -10, 20, winSizeV))
        self.SetResDivider.setFrameShape(QFrame.Shape.VLine)
        self.SetResDivider.setFrameShadow(QFrame.Shadow.Sunken)

        self.CommentsTextBrowser = QTextBrowser(parent=self.SetResTab)
        self.CommentsTextBrowser.setGeometry(QRect(self.col0x, self.coly*9, int(self.lbl_width*3.2), self.lbl_height*2))
        self.CommentsTextBrowser.setReadOnly(False)

        self.progressBar = QProgressBar(parent=self.centralwidget)
        self.progressBar.setGeometry(QRect(self.col7x, self.coly*4, self.lbl_width, self.lbl_height))
        self.progressBar.setProperty("value", 0)

    def retranslateUi(self, mainWindow) -> None:
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
        self.StandardRLabel.setText(_translate("mainWindow", "Standard R"))
        self.MeasTimeLabel.setText(_translate("mainWindow", "Measurement Time"))
        self.RemTimeLabel.setText(_translate("mainWindow", "Remaining Time"))
        self.ReadingDelayLabel.setText(_translate("mainWindow", "Reading Delay [s]"))
        self.SquidFeedLabel.setText(_translate("mainWindow", "Squid Feed In"))
        self.StandardRBut.setText(_translate("mainWindow", "R1"))
        self.R1TotalPresLabel.setText(_translate("mainWindow", "R1 Total Pressure [Pa]"))
        self.VMeanLabel.setText(_translate("mainWindow", "Mean [V]"))
        self.RMeanChkPPMLabel.setText(_translate("mainWindow", "R Mean Chk (ppm)"))
        self.C2Label.setText(_translate("mainWindow", "C2 (ppm)"))
        self.StdDevMeanLabel.setText(_translate("mainWindow", "Std. Mean [ppm]"))
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
        self.MeasLabel.setText(_translate("mainWindow", "Meas [s]\Delay [s]"))
        self.SampUsedLabel.setText(_translate("mainWindow", "Samples Used"))
        self.ResultsLabel.setText(_translate("mainWindow", "RESULTS"))
        self.SquidFeedBut.setText(_translate("mainWindow", "Negative"))
        self.SettingsLabel.setText(_translate("mainWindow", "SETTINGS"))
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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SpecTab), _translate("mainWindow", "Power Spec."))
        self.txtFileLabel.setText(_translate("mainWindow", ".txt File"))
        self.VMeanChkLabel.setText(_translate("mainWindow", "Mean Chk [V]"))
        self.StdDevChkLabel.setText(_translate("mainWindow", "Std. Dev. Chk"))
        self.StdDevMeanChkLabel.setText(_translate("mainWindow", "Std. Mean Chk"))
        self.saveButton.setText(_translate("mainWindow", "Save"))
        self.MDSSButton.setText(_translate("mainWindow", "No"))
        self.MDSSLabel.setText(_translate("mainWindow", "Save MDSS"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))

    def plotBVD(self) -> None:
        if self.bvd is not None:
            if self.plottedBVD:
                self.clearBVDPlot()
            self.plottedBVD = True
            count = range(len(self.bvd.A))
            self.BVDax1.scatter(count, self.bvd.A, color='r', marker='+', s=75)
            self.BVDax1.scatter(count, self.bvd.B, color='b', marker='x')
            self.BVDax1.set_xlabel('Count')
            self.BVDax1.set_ylabel('Amplitude [V]')
            self.BVDax1.legend(['I+', 'I-'])
            self.BVDax1.grid(alpha=self.alpha)
            if self.RButStatus == 'R1':
                self.BVDax2.scatter(self.bvdCount, self.bvd.R1List, color='b', zorder=3, label='Resistance')
            else:
                self.BVDax2.scatter(self.bvdCount, self.bvd.R2List, color='b', zorder=3, label='Resistance')
    
            self.BVDax2.set_xlabel('Count')
            if self.RButStatus == 'R1':
                self.BVDax2.set_ylabel('R2 [ppm]', color='b')
            else:
                self.BVDax2.set_ylabel('R1 [ppm]', color='b')
    
            self.BVDtwin2 = self.BVDax2.twinx()
            self.BVDax2.tick_params(axis='y', colors='b')
            self.BVDtwin2.tick_params(axis='y', direction='in', colors='r')
            self.BVDtwin2.set_yticklabels([])
            if self.bvd.bvdList:
                BVDmean = mean(self.bvd.bvdList)
                BVDstd  = std(self.bvd.bvdList, ddof=1)
                upper   =  3*BVDstd + BVDmean
                lower   = -3*BVDstd + BVDmean
                self.BVDtwin2.plot(self.bvdCount, upper*ones(len(self.bvd.bvdList), dtype=int), color='r', linestyle='--')
                self.BVDtwin2.plot(self.bvdCount, lower*ones(len(self.bvd.bvdList), dtype=int), color='r', linestyle='--')
                self.BVDtwin2.scatter(self.bvdCount, self.bvd.bvdList, color='r', label='BVD')
    
                self.BVDax3.hist(self.bvd.bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                self.BVDax3.xaxis.set_major_locator(MaxNLocator(integer=True))
                self.BVDax3.set_ylim([self.BVDtwin2.get_ylim()[0], self.BVDtwin2.get_ylim()[1]])
                self.BVDax3.tick_params(axis='y', colors='r')
                # self.BVDax3.set_yticklabels([])
                self.BVDax3.yaxis.tick_right()
                self.BVDax3.set_ylabel('BVD [V]', color='r')
                self.BVDax3.yaxis.set_label_position('right')
            else:
                self.BVDax2.cla()
                self.BVDax3.cla()
    
            # self.BVDtwin2.set_ylabel('BVD [V]', color='r')
            self.BVDax2.set_axisbelow(True)
            self.BVDax2.grid(axis='x', zorder=0, alpha=self.alpha)
            self.BVDax2.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.BVDtwin2.set_axisbelow(True)
            self.BVDtwin2.grid(zorder=0, alpha=self.alpha)
    
            lines, labels   = self.BVDax2.get_legend_handles_labels()
            lines2, labels2 = self.BVDtwin2.get_legend_handles_labels()
            self.BVDax2.legend(lines + lines2, labels + labels2)
    
            # self.BVDfig.tight_layout()
            self.BVDfig.set_tight_layout(True)
            self.BVDcanvas.draw()
    
            self.SkewnessEdit.setText(str("{:.3f}".format(skewness(self.bvd.bvdList))))
            self.KurtosisEdit.setText(str("{:.3f}".format(kurtosis(self.bvd.bvdList))))

    def plotAllan(self) -> None:
        if self.plottedAllan:
            self.clearAllanPlot()
        self.plottedAllan = True
        overlapping = is_overlapping(self.OverlappingComboBox.currentText())
        if self.bvd.bvdList:
            if self.AllanTypeComboBox.currentText() == '2^n':
                tau_list = powers_of_2(int(len(self.bvd.bvdList)//2))
            elif self.AllanTypeComboBox.currentText() == 'all':
                tau_list = list(map(int, linspace(1, len(self.bvd.bvdList)//2, len(self.bvd.bvdList)//2)))
            bvd_tau, bvd_adev, bvd_aerr = mystat.adev(array(self.bvd.bvdList), overlapping, tau_list)
            if self.RButStatus == 'R1':
                if self.AllanTypeComboBox.currentText() == '2^n':
                    tau_list_C1 = powers_of_2(int(len(self.bvd.C1R2List)//2))
                    tau_list_C2 = powers_of_2(int(len(self.bvd.C2R2List)//2))
                elif self.AllanTypeComboBox.currentText() == 'all':
                    tau_list_C1 = list(map(int, linspace(1, len(self.bvd.C1R2List)//2, len(self.bvd.C1R2List)//2)))
                    tau_list_C2 = list(map(int, linspace(1, len(self.bvd.C2R2List)//2, len(self.bvd.C2R2List)//2)))
                C1_tau, C1_adev, C1_aerr = mystat.adev(array(self.bvd.C1R2List), overlapping, tau_list_C1)
                C2_tau, C2_adev, C2_aerr = mystat.adev(array(self.bvd.C2R2List), overlapping, tau_list_C2)
            else:
                if self.AllanTypeComboBox.currentText() == '2^n':
                    tau_list_C1 = powers_of_2(int(len(self.bvd.C1R1List)//2))
                    tau_list_C2 = powers_of_2(int(len(self.bvd.C2R1List)//2))
                elif self.AllanTypeComboBox.currentText() == 'all':
                    tau_list_C1 = list(map(int, linspace(1, len(self.bvd.C1R1List)//2, len(self.bvd.C1R1List)//2)))
                    tau_list_C2 = list(map(int, linspace(1, len(self.bvd.C2R1List)//2, len(self.bvd.C2R1List)//2)))
                C1_tau, C1_adev, C1_aerr = mystat.adev(array(self.bvd.C1R1List), overlapping, tau_list_C1)
                C2_tau, C2_adev, C2_aerr = mystat.adev(array(self.bvd.C2R1List), overlapping, tau_list_C2)
            if self.AllanTypeComboBox.currentText() == '2^n':
                tau_list_bvda = powers_of_2(int(len(self.bvd.A)//2))
                tau_list_bvdb = powers_of_2(int(len(self.bvd.B)//2))
            elif self.AllanTypeComboBox.currentText() == 'all':
                tau_list_bvda = list(map(int, linspace(1, len(self.bvd.A)//2, len(self.bvd.A)//2)))
                tau_list_bvdb = list(map(int, linspace(1, len(self.bvd.B)//2, len(self.bvd.B)//2)))
            bvda_tau, bvda_adev, bvda_aerr = mystat.adev(array(self.bvd.A), overlapping, tau_list_bvda)
            bvdb_tau, bvdb_adev, bvdb_aerr = mystat.adev(array(self.bvd.B), overlapping, tau_list_bvdb)

            self.Allanax1.plot(bvd_tau, bvd_adev, color='b')
            self.Allanax2.plot(C1_tau, C1_adev, color='b')
            self.Allanax3.plot(C2_tau, C2_adev, color='b')
            self.Allanax4.plot(bvda_tau, bvda_adev, color='b')
            self.Allanax4.plot(bvdb_tau, bvdb_adev, color='r')
        else:
            self.clearAllanPlot()

        if self.validFile:
            self.Allanax1.set_ylabel('\u03C3(\u03C4), BVD [V]')
            self.Allanax1.set_xlabel('\u03C4 (samples)')
            self.Allanax1.set_yscale('log')
            self.Allanax1.set_xscale('log')
            self.Allanax1.grid(which='both', alpha=.25)
            # self.Allanax1.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.Allanax1.xaxis.set_major_formatter(ScalarFormatter())

            self.Allanax2.set_ylabel('\u03C3(\u03C4), C1 [V]')
            self.Allanax2.set_xlabel('\u03C4 (samples)')
            self.Allanax2.set_yscale('log')
            self.Allanax2.set_xscale('log')
            self.Allanax2.grid(which='both', alpha=self.alpha)
            # self.Allanax2.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.Allanax2.xaxis.set_major_formatter(ScalarFormatter())

            self.Allanax3.set_ylabel('\u03C3(\u03C4), C2 [V]')
            self.Allanax3.set_xlabel('\u03C4 (samples)')
            self.Allanax3.set_yscale('log')
            self.Allanax3.set_xscale('log')
            self.Allanax3.grid(which='both', alpha=self.alpha)
            # self.Allanax3.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.Allanax3.xaxis.set_major_formatter(ScalarFormatter())

            self.Allanax4.set_ylabel('\u03C3(\u03C4), BV [V]')
            self.Allanax4.set_xlabel('\u03C4 (samples)')
            self.Allanax4.set_yscale('log')
            self.Allanax4.set_xscale('log')
            self.Allanax4.legend(['I+', 'I-'])
            self.Allanax4.grid(which='both', alpha=self.alpha)
            # self.Allanax4.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.Allanax4.xaxis.set_major_formatter(ScalarFormatter())

            self.Allanfig.set_tight_layout(True)
            self.AllanCanvas.draw()

    def plotSpec(self) -> None:
        samp_freq = 1/(self.dat.meas)
        # print (samp_freq)
        if self.plottedSpec:
            self.clearPlots()
        # Create the window function
        mywindow_mystat = mystat.hann(float(samp_freq), (len(self.bvd.bvdList)*float(samp_freq)))
        freq_bvd, mypsa_bvd = mystat.fft(1./(float(samp_freq)), array(self.bvd.bvdList), array(mywindow_mystat))
        self.SpecAx.set_title('Power Spectrum')
        self.SpecAx.set_ylabel('Magnitude')
        self.SpecAx.set_xlabel('Frequency (Hz)')
        self.SpecAx.grid(alpha=self.alpha)

        self.PowerSpecAx.set_title('Power Spectrum from FFT')
        self.PowerSpecAx.set_ylabel('Magnitude')
        self.PowerSpecAx.set_xlabel('Frequency (Hz)')
        self.PowerSpecAx.grid(alpha=self.alpha)

        self.SpecAx.plot(freq_bvd, mypsa_bvd)

        self.Specfig.set_tight_layout(True)
        self.SpecCanvas.draw()

    def clearBVDPlot(self) -> None:
        self.BVDax2.cla()
        try:
            self.BVDtwin2.remove()
            self.BVDtwin2.set_visible(False)
        except (AttributeError, KeyError):
            pass
        self.BVDcanvas.draw()
        self.plottedBVD = False

    def clearAllanPlot(self) -> None:
        self.Allanax1.cla()
        self.Allanax2.cla()
        self.Allanax3.cla()
        self.Allanax4.cla()
        self.AllanCanvas.draw()
        self.plottedAllan = False

    def clearPlots(self) -> None:
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

        self.SpecAx.cla()
        self.SpecCanvas.draw()

        self.plottedBVD, self.plottedAllan, self.plottedSpec = False, False, False

    def RButClicked(self) -> None:
        if self.StandardRBut.pressed and self.RButStatus == 'R1':
            self.RButStatus = 'R2'
            self.StandardRBut.setText('R2')
            self.StandardRBut.setStyleSheet(green_style)
            if self.validFile:
                self.stdR(self.RButStatus)
        else:
            self.RButStatus = 'R1'
            self.StandardRBut.setText('R1')
            self.StandardRBut.setStyleSheet(red_style)
            if self.validFile:
                self.stdR(self.RButStatus)
        self.plotBVD()
        

    def SquidButClicked(self) -> None:
        if self.SquidFeedBut.pressed and self.SquidFeedStatus == 'NEG':
            self.SquidFeedStatus = 'POS'
            self.SquidFeedBut.setText('Positive')
            self.SquidFeedBut.setStyleSheet(red_style)
        else:
            self.SquidFeedStatus = 'NEG'
            self.SquidFeedBut.setText('Negative')
            self.SquidFeedBut.setStyleSheet(blue_style)

    def CurrentButClicked(self) -> None:
        if self.CurrentBut.pressed and self.CurrentButStatus == 'I1':
            self.CurrentButStatus = 'I2'
            self.CurrentBut.setText('I2')
            self.CurrentBut.setStyleSheet(blue_style)
        else:
            self.CurrentButStatus = 'I1'
            self.CurrentBut.setText('I1')
            self.CurrentBut.setStyleSheet(red_style)

    def getData(self) -> None:
        if self.txtFilePath.endswith('.txt') and os.path.exists(self.txtFilePath) and self.txtFilePath.split('.txt')[0][-1].isnumeric():
            self.validFile = True
            if '/' in self.txtFilePath:
                self.txtFile = self.txtFilePath.split('/')[-1]
            else:
                self.txtFile = self.txtFilePath.split('\\')[-1]
            self.dat = magnicon_ccc(self.txtFilePath)
            self.bvd = bvd_stat(self.txtFilePath, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.data = True
        else:
            self.setInvalidData()
            self.data = False

    def setValidData(self) -> None:
        if self.plottedBVD or self.plottedAllan or self.plottedSpec:
            self.plottedBVD   = False
            self.plottedAllan = False
            self.plottedSpec  = False
            self.clearPlots()
        self.VMeanLineEdit.setText(str("{:.6e}".format(self.dat.bvdMean)))
        self.VMeanChkLineEdit.setText(str("{:.6e}".format(self.bvd.mean)))
        self.Current1LineEdit.setText(str(self.dat.I1))
        self.FullCycLineEdit.setText(str(self.dat.fullCyc))
        self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))
        self.MeasLineEdit.setText(str("{:2.4f}".format(self.dat.meas)) + '\\' + str(self.dat.delay))
        self.R1SNLineEdit.setText(self.dat.R1SN)
        self.Current2LineEdit.setText(str(self.dat.I2))
        self.N2LineEdit.setText(str(self.dat.N2))
        self.NAuxLineEdit.setText(str(self.dat.NA))
        self.AppVoltLineEdit.setText(str("{:.6}".format(self.dat.appVolt)))
        self.R2SNLineEdit.setText(self.dat.R2SN)
        self.SHCLineEdit.setText(str(self.dat.SHC))
        self.N1LineEdit.setText(str(self.dat.N1))
        self.CommentsTextBrowser.setText(self.dat.comments)
        self.RelHumLineEdit.setText(str(self.dat.relHum))
        self.ReadingDelaySpinBox.setValue(10)

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

        self.MDSSButton.setStyleSheet(red_style)
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
        self.plotBVD()
        self.plotAllan()
        self.plotSpec()

    def setInvalidData(self) -> None:
        self.validFile = False
        self.VMeanLineEdit.setText("")
        self.VMeanChkLineEdit.setText("")
        self.Current1LineEdit.setText("")
        self.FullCycLineEdit.setText("")
        self.MeasCycLineEdit.setText("")
        self.SampUsedLineEdit.setText("")
        self.RampLineEdit.setText("")
        self.MeasLineEdit.setText("")
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
        self.ReadingDelaySpinBox.setValue(0)

        self.MDSSButton.setStyleSheet("")
        self.MDSSButton.setText("No")
        self.MDSSButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.saveStatus = False

        self.SkewnessEdit.setText("")
        self.KurtosisEdit.setText("")

        self.deletedIndex = []
        self.deletedCount = []
        self.deletedBVD   = []
        self.bvdCount     = []
        self.deletedR1    = []
        self.deletedR2    = []

        self.plotCountCombo.clear()

        if self.plottedBVD or self.plottedAllan or self.plottedSpec:
            self.plottedBVD   = False
            self.plottedAllan = False
            self.plottedSpec  = False
            self.clearPlots()

    def stdR(self, R: str) -> None:
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

    def R1PresChanged(self) -> None:
        try:
            try:
                self.R1pres    = int(self.R1PresLineEdit.text())
                self.R1TotPres = self.R1pres + self.R1OilPres
                self.getData()
            except ValueError:
                self.R1pres    = float(self.R1PresLineEdit.text())
                self.R1TotPres = self.R1pres + self.R1OilPres
                self.getData()
        except ValueError:
            self.R1PresLineEdit.setText(str(self.R1pres))

    def R2PresChanged(self) -> None:
        try:
            try:
                self.R2pres    = int(self.R2PresLineEdit.text())
                self.R2TotPres = self.R2pres + self.R2OilPres
                self.getData()
            except ValueError:
                self.R2pres    = float(self.R2PresLineEdit.text())
                self.R2TotPres = self.R2pres + self.R2OilPres
                self.getData()
        except ValueError:
            self.R2PresLineEdit.setText(str(self.R2pres))

    def oilDepth1Changed(self) -> None:
        self.R1OilDepth = self.R1OilDepthSpinBox.value()
        if self.R1PresLineEdit.text():
            self.updateOilDepth('R1')
            self.getData()

    def oilDepth2Changed(self) -> None:
        self.R2OilDepth = self.R2OilDepthSpinBox.value()
        if self.R2PresLineEdit.text():
            self.updateOilDepth('R2')
            self.getData()

    def updateOilDepth(self, R: str) -> None:
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

    def temp1Changed(self) -> None:
        try:
            self.R1Temp = float(self.R1TempLineEdit.text())
            self.getData()
        except ValueError:
            self.R1TempLineEdit.setText(str("{:.4f}".format(self.R1Temp)))

    def temp2Changed(self) -> None:
        try:
            self.R2Temp = float(self.R2TempLineEdit.text())
            self.getData()
        except ValueError:
            self.R2TempLineEdit.setText(str("{:.4f}".format(self.R2Temp)))

    def folderClicked(self) -> None:
        if self.dialog.exec():
            self.txtFilePath = self.dialog.selectedFiles()[0]
            print(self.txtFilePath)
        # self.txtFilePath = filedialog.askopenfilename()
        # print(self.txtFilePath)
        # tkinter.Tk().withdraw()
        self.txtFileLineEdit.setText(self.txtFilePath)
        self.getData()

    def folderEdited(self) -> None:
        self.txtFilePath = self.txtFileLineEdit.text()
        self.getData()

    def MDSSClicked(self) -> None:
        if self.saveStatus:
            self.saveStatus = False
            self.MDSSButton.setStyleSheet(red_style)
            self.MDSSButton.setText('No')
            self.saveButton.setEnabled(False)
        else:
            self.saveStatus = True
            self.MDSSButton.setStyleSheet(green_style)
            self.MDSSButton.setText('Yes')
            self.saveButton.setEnabled(True)
            self.progressBar.setProperty('value', 0)

    def saveMDSS(self) -> None:
        self.progressBar.setProperty('value', 25)
        self.saveStatus = False
        self.MDSSButton.setStyleSheet(red_style)
        self.MDSSButton.setText('No')
        self.saveButton.setEnabled(False)
        self.dat.comments = self.CommentsTextBrowser.toPlainText()
        self.createDataFile()
        self.progressBar.setProperty('value', 100)

    def createDataFile(self) -> None:
        writeDataFile(text=self.txtFile, dat_obj=self.dat, bvd_stat_obj=self.bvd, RStatus=self.RButStatus, R1Temp=self.R1Temp,
                      R2Temp=self.R2Temp, R1Pres=self.R1TotPres, R2Pres=self.R2TotPres, I=self.CurrentButStatus, polarity=self.SquidFeedStatus,
                      system=self.MagElecComboBox.currentText(), probe=self.ProbeComboBox.currentText())

    def tabIndexChanged(self) -> None:
        return
        # if self.tabWidget.currentIndex() == 1 and self.validFile:
        #     self.plotBVD()
        # elif self.tabWidget.currentIndex() == 2 and self.validFile and not self.plottedAllan:
        #     self.plotAllan()
        # elif self.tabWidget.currentIndex() == 3 and self.validFile:
        #     self.plotSpec()

    def deleteBut(self) -> None:
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
            self.plotAllan()

    def restoreDeleted(self, loop=None) -> None:
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
                self.plotAllan()

    def replotAll(self) -> None:
        looped = False
        while(self.deletedCount):
            self.restoreDeleted(loop=True)
            looped = True
        if looped:
            self.plotBVD()
            self.plotAllan()

def is_overlapping(overlapping: str) -> bool:
    if overlapping == 'overlapping':
        return True
    else:
        return False

def powers_of_2(n: int) -> list:
    x   = 1
    arr = []
    while(x < n):
        arr.append(x)
        x = x*2
    return arr

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    mainWindow.setWindowTitle("Magnicon Offline Analyzer " + __version__)
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec())