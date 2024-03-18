import sys, os
from time import perf_counter
import inspect

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QRect, QMetaObject, QCoreApplication
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainterPath, QPainter,\
                        QKeySequence, QDoubleValidator, QIntValidator
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, \
                             QLabel, QPushButton, QComboBox, QTextBrowser, QTabWidget, \
                             QSpacerItem, QGridLayout, QLineEdit, QFrame, QSizePolicy, \
                             QMenuBar, QSpinBox, QProgressBar, QToolButton, QStatusBar, \
                             QTextEdit, QFileDialog)

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import MaxNLocator, ScalarFormatter
import matplotlib.style as mplstyle
from numpy import sqrt, std, mean, ones, linspace, array, nan
from scipy import signal
import allantools

# custom imports
from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
from create_mag_ccc_datafile import writeDataFile
import mystat

# python globals
__version__ = '1.6.1' # Program version string
red_style   = "color: white; background-color: red"
blue_style  = "color: white; background-color: blue"
green_style = "color: white; background-color: green"
winSizeH    = 1000
winSizeV    = 835
c           = 0.8465 # specific gravity of oil used
g           = 9.81 # local acceleration due to gravity

params = {
           'axes.labelsize': 14,
           'font.size': 10,
           'text.usetex': False,
           'legend.fontsize': 12,
           'xtick.labelsize': 12,
           'ytick.labelsize': 12,
           'figure.max_open_warning': 20,
           'figure.facecolor': 'white',
           'figure.edgecolor': 'white',
           'axes.spines.top': True,
           'axes.spines.bottom': True,
           'axes.spines.left': True,
           'axes.spines.right': True,
           'grid.color': 'gray',
           'grid.linestyle': '-',
           'grid.alpha': 0.2,
           'grid.linewidth': 0.8,
           'axes.formatter.use_mathtext' : True,
           # 'text.latex.preamble': [r'\usepackage{siunitx}']
         }
plt.rc('axes', linewidth=2)
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.it'] = 'STIXGeneral:italic'
plt.rcParams['mathtext.bf'] = 'STIXGeneral:italic:bold'
plt.rcParams["font.family"] = "Times New Roman"

mpl.rcParams.update(params)
mplstyle.use('fast')

# base directory of the project
if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_dir = sys._MEIPASS
    # base_dir = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
    import pyi_splash
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
        # print('Class: aboutWindow, In function: ' + inspect.stack()[0][3])
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

class timingDiagramWindow(QWidget):
    def __init__(self):
        """QWidget class for showing the timing diagram window to display CCC's
           sampling routing
        """
        super(QWidget, self).__init__()
        self.setFixedSize(1120, 550)
        lbl_timing_diagram = QLabel(self)
        lbl_timing_diagram.setPixmap(QPixmap(base_dir + r"\icons\timing_diagram.PNG"))
        lbl_timing_diagram.show()
        layout = QVBoxLayout()
        layout.addWidget(lbl_timing_diagram)
        self.setLayout(layout)

class Ui_mainWindow(object):
    def setupUi(self, mainWindow) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        global winSizeH, winSizeV
        mainWindow.setFixedSize(winSizeH, winSizeV)
        mainWindow.setWindowIcon(QIcon(base_dir + r'\icons\analyzer.ico'))
        self.initializations()

        self.centralwidget = QWidget(parent=mainWindow)
        self.tabWidget = QTabWidget(parent=self.centralwidget)
        self.tabWidget.setGeometry(QRect(0, 0, winSizeH - 125, winSizeV))
        self.SetResTab = QWidget()
        self.SetResTab.paintEvent = lambda event: self._paintPath(event)
        self.tabWidget.addTab(self.SetResTab, "")
        # drawing pens
        self.red_pen = QtGui.QPen()
        self.red_pen.setWidth(4)
        self.red_pen.setColor(QtGui.QColor('red'))

        self.black_pen = QtGui.QPen()
        self.black_pen.setWidth(4)
        self.black_pen.setColor(QtGui.QColor('black'))

        self.green_pen = QtGui.QPen()
        self.green_pen.setWidth(4)
        self.green_pen.setColor(QtGui.QColor('green'))

        # initialize QWidgets
        self.setLabels()
        self.setLineEdits()
        self.setSpinBoxes()
        self.setComboBoxes()
        self.setMisc()
        self.setButtons()
        self.BVDTabSetUp()
        self.AllanTabSetUp()
        self.SpecTabSetUp()

        # options and actions for the top window menu
        self.file_action = QAction("&Open...")
        self.file_action.setStatusTip("Open data file")
        self.file_action.triggered.connect(self.folderClicked)
        # self.file_action.setCheckable(True)
        self.file_action.setShortcut(QKeySequence("Ctrl+o"))
        self.file_action.setShortcutVisibleInContextMenu(True)

        self.close_action = QAction("&Quit")
        self.close_action.setStatusTip("Quit this program")
        self.close_action.triggered.connect(self.quit)
        # self.close_action.setCheckable(True)
        self.close_action.setShortcut(QKeySequence("Ctrl+q"))

        self.about_action = QAction("&About")
        self.about_action.setStatusTip("Program information & license")
        self.about_action.triggered.connect(self._about)
        
        self.timing_action = QAction("&Timing Diagram")
        self.timing_action.setStatusTip("Show timing diagram for CCC Measurements")
        self.timing_action.triggered.connect(self._showTimingDiagram)
        
        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(parent=mainWindow)
        self.menubar.setGeometry(QRect(0, 0, winSizeH, 22))
        self._create_menubar()
        mainWindow.setMenuBar(self.menubar)

        self.dialog = QFileDialog(parent=mainWindow, )
        # self.dialog.setViewMode(QFileDialog.Detail)
        if os.path.exists(r"\\elwood.nist.gov\68internal\Calibrations\MDSS Data\resist"):
            self.dialog.setDirectory(r"\\elwood.nist.gov\68internal\Calibrations\MDSS Data\resist\MagniconData\CCCViewerData")
        else:
            self.dialog.setDirectory(r"C:")
        self.dialog.setNameFilters(["Text files (*_bvd.txt)"])
        self.dialog.selectNameFilter("Text files (*_bvd.txt)")

        self.statusbar = QStatusBar(parent=mainWindow)
        mainWindow.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready", 2000)

        self.retranslateUi(mainWindow)
        self.tabWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(mainWindow)
        # self.drawTimingDiagram()
        if getattr(sys, 'frozen', False):
            pyi_splash.close()

    def drawTimingDiagram(self,):
        self.path = QPainterPath()
        self.shift_col4x = self.col4x - 5
        self.path.moveTo(self.shift_col4x, 400)
        self.path.lineTo(self.shift_col4x + 50, 350)
        self.path.lineTo(self.shift_col4x + 350, 350)

    def _paintPath(self, event):
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        ramp_max = 100 # 100 pixels  corresponds to 10s of ramp time which is max
        y_start = 400
        y_end = 350
        painter = QPainter(self.SetResTab)
        # painter.begin(self.SetResTab)
        painter.setPen(self.black_pen)
        scale_factor = 1.0
        painter.scale(scale_factor, scale_factor)
        if self.SampUsedLineEdit.text() != '':
            self.path = QPainterPath()
            self.shift_col4x = self.col4x - 5
            self.path.clear()
            self.path.moveTo(self.shift_col4x, y_start)
            rx = int(int(self.dat.rampTime)*ramp_max/10) # calculate rx based on ramp time
            self.path.lineTo(self.shift_col4x + rx, y_end)
            if rx != 0:
                slope = int((y_start - y_end)/rx)
            else:
                slope = 1
            self.path.lineTo(self.shift_col4x + rx + y_end, y_end)
            painter.drawPath(self.path)
            for ct, i in enumerate(linspace(self.shift_col4x, self.shift_col4x + y_end, num=int(self.dat.SHC))):
                painter.setPen(self.red_pen)
                if i < self.shift_col4x + rx:
                    painter.drawPoint(int(i), y_start - slope*int(i))
                else:
                    painter.drawPoint(int(i), 350)
                # draw green line for samples used
                if ct >= (int(self.dat.SHC) -  int(self.SampUsedLineEdit.text())):
                    painter.setPen(self.green_pen)
                    painter.drawLine(int(i), 355, int(i), 400)
        painter.end()

    def _create_menubar(self, ) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(self.file_action)
        self.file_menu.addAction(self.close_action)
        # self.file_menu.setShortcutEnabled(True)
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(self.about_action)
        self.help_menu.addAction(self.timing_action)
        

    def _about(self,) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.about_window = aboutWindow()
        self.about_window.show()
    
    def _showTimingDiagram(self, ) -> None:
        self.timing_window = timingDiagramWindow()
        self.timing_window.show()

    def closeEvent(self, event):
        mainWindow.close()
        self.quit()
        event.accept()

    def quit(self,) -> None:
        """
        Quit the application

        Returns
        -------
        None.
        """
        mainWindow.close()
        QtCore.QCoreApplication.instance().quit
        app.quit()

    def initializations(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.txtFilePath  = ''
        # flags
        self.validFile    = False
        self.plottedBVD   = False
        self.plottedAllan = False
        self.plottedSpec  = False
        self.changedDeltaI2R2Ct = 0
        self.changedR1STPBool = False
        self.changedR2STPBool = False

        self.R1Temp     = 23
        self.R2Temp     = 23
        self.R1pres     = 101325
        self.R2pres     = 101325
        self.R1OilDepth = 0
        self.R2OilDepth = 0
        self.alpha      = 0.5
        self.R1OilPres  = 0.8465*9.81*self.R1OilDepth
        self.R2OilPres  = 0.8465*9.81*self.R2OilDepth
        self.R1TotPres  = self.R1pres + self.R1OilPres
        self.R2TotPres  = self.R2pres + self.R2OilPres

        self.RButStatus       = 'R1'
        self.SquidFeedStatus  = 'NEG'
        self.CurrentButStatus = 'I2'
        self.saveStatus       = False

        self.bvdCount     = []
        self.deletedIndex = []
        self.deletedCount = []
        self.deletedBVD   = []
        self.deletedR1    = []
        self.deletedR2    = []
        self.dat          = None # magnicon_ccc class object
        self.bvd_stat_obj = None # bvd_stats class object

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
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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
        self.DelayLabel = QLabel(parent=self.SetResTab)
        self.DelayLabel.setGeometry(QRect(self.col2x, 270, self.lbl_width, self.lbl_height))
        self.MeasLabel = QLabel(parent=self.SetResTab)
        self.MeasLabel.setGeometry(QRect(self.col2x, 330, self.lbl_width, self.lbl_height))
        self.R1OilPresLabel = QLabel(parent=self.SetResTab)
        self.R1OilPresLabel.setGeometry(QRect(self.col2x, 390, self.lbl_width, self.lbl_height))
        self.R2OilPresLabel = QLabel(parent=self.SetResTab)
        self.R2OilPresLabel.setGeometry(QRect(self.col2x, 450, self.lbl_width, self.lbl_height))
        # col3
        self.kLabel = QLabel(parent=self.SetResTab)
        self.kLabel.setGeometry(QRect(self.col3x, 30, self.lbl_width, self.lbl_height))
        self.MeasTimeLabel = QLabel(parent=self.SetResTab)
        self.MeasTimeLabel.setGeometry(QRect(self.col3x, 90, self.lbl_width, self.lbl_height))
        self.lbl_deltaI2R2 = QLabel(parent=self.SetResTab)
        self.lbl_deltaI2R2.setGeometry(QRect(self.col3x, 150, self.lbl_width, self.lbl_height))
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
        # col6
        self.R1STPLabel = QLabel(parent=self.SetResTab)
        self.R1STPLabel.setGeometry(QRect(self.col6x, 30, self.lbl_width, self.lbl_height))
        self.R2STPLabel = QLabel(parent=self.SetResTab)
        self.R2STPLabel.setGeometry(QRect(self.col6x, 90, self.lbl_width, self.lbl_height))
        self.NLabel = QLabel(parent=self.SetResTab)
        self.NLabel.setGeometry(QRect(self.col6x, 150, self.lbl_width, self.lbl_height))
        self.StdDevPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevPPMLabel.setGeometry(QRect(self.col6x, 210, self.lbl_width, self.lbl_height))
        self.StdDevChkPPMLabel = QLabel(parent=self.SetResTab)
        self.StdDevChkPPMLabel.setGeometry(QRect(self.col6x, 270, self.lbl_width, self.lbl_height))
        # col7
        self.StandardRLabel = QLabel(parent=self.centralwidget)
        self.StandardRLabel.setGeometry(QRect(self.col7x, 30, self.lbl_width, self.lbl_height))
        self.MDSSLabel = QLabel(parent=self.centralwidget)
        self.MDSSLabel.setGeometry(QRect(self.col7x, 90, self.lbl_width, self.lbl_height))
        self.ppmMeanLabel = QLabel(parent=self.centralwidget)
        self.ppmMeanLabel.setGeometry(QRect(self.col7x, 270, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLabel = QLabel(parent=self.centralwidget)
        self.RMeanChkPPMLabel.setGeometry(QRect(self.col7x, 330, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLabel = QLabel(parent=self.centralwidget)
        self.StdDevMeanPPMLabel.setGeometry(QRect(self.col7x, 390, self.lbl_width, self.lbl_height))
        self.C1C2Label = QLabel(parent=self.centralwidget)
        self.C1C2Label.setGeometry(QRect(self.col7x, 450, self.lbl_width, self.lbl_height))
        self.RatioMeanLabel = QLabel(parent=self.centralwidget)
        self.RatioMeanLabel.setGeometry(QRect(self.col7x, 510, self.lbl_width, self.lbl_height))
        self.SampUsedLabel = QLabel(parent=self.centralwidget)
        self.SampUsedLabel.setGeometry(QRect(self.col7x, 570, self.lbl_width, self.lbl_height))
        self.ResultsLabel = QLabel(parent=self.SetResTab)
        self.ResultsLabel.setGeometry(QRect(650, 10, self.lbl_width, self.lbl_height))
        self.ResultsLabel.setStyleSheet(
                """QLabel {color: blue; font-weight: bold; font-size: 14pt }""")
        self.SettingsLabel = QLabel(parent=self.SetResTab)
        self.SettingsLabel.setGeometry(QRect(220, 10, self.lbl_width, self.lbl_height))
        self.SettingsLabel.setStyleSheet(
                """QLabel {color: red; font-weight: bold; font-size: 14pt }""")
        self.lbl_ccceq = QLabel(parent=self.SetResTab)
        self.lbl_ccceq.setGeometry(QRect(640, 440, self.lbl_width+25, self.lbl_height))
        self.lbl_ccceq.setStyleSheet(
                """QLabel {color: green; font-weight: bold; font-size: 14pt }""")
        self.LogoLabel = QLabel(parent=self.SetResTab)
        self.LogoPixmap = QPixmap(base_dir + r'\icons\nist_logo.png')
        self.LogoLabel.setPixmap(self.LogoPixmap)
        self.LogoLabel.setGeometry(QRect(550, 700, 300, 76))

        self.lbl_equation = QLabel(parent=self.SetResTab)
        self.pixmap_equation = QPixmap(base_dir + r'\icons\ccc_equation.PNG')
        self.lbl_equation.setPixmap(self.pixmap_equation)
        self.lbl_equation.setGeometry(QRect(550, 475, 314, 222))

    def setLineEdits(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        # col0
        self.R1SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1SNLineEdit.setGeometry(QRect(self.col0x, self.coly, self.lbl_width, self.lbl_height))
        self.R1SNLineEdit.setReadOnly(True)
        self.R1SNLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R2SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2SNLineEdit.setGeometry(QRect(self.col0x, self.coly*2 , self.lbl_width, self.lbl_height))
        self.R2SNLineEdit.setReadOnly(True)
        self.R2SNLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.AppVoltLineEdit = QLineEdit(parent=self.SetResTab)
        self.AppVoltLineEdit.setGeometry(QRect(self.col0x, self.coly*3, self.lbl_width, self.lbl_height))
        self.AppVoltLineEdit.setReadOnly(True)
        self.AppVoltLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.N1LineEdit = QLineEdit(parent=self.SetResTab)
        self.N1LineEdit.setGeometry(QRect(self.col0x, self.coly*4, self.lbl_width, self.lbl_height))
        self.N1LineEdit.setReadOnly(True)
        self.N1LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.MeasCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasCycLineEdit.setGeometry(QRect(self.col0x, self.coly*5, self.lbl_width, self.lbl_height))
        self.MeasCycLineEdit.setReadOnly(True)
        self.MeasCycLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.FullCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.FullCycLineEdit.setGeometry(QRect(self.col0x, self.coly*6, self.lbl_width, self.lbl_height))
        self.FullCycLineEdit.setReadOnly(True)
        self.FullCycLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
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
        self.R1PPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R2PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PPMLineEdit.setGeometry(QRect(self.col1x, self.coly*2, self.lbl_width, self.lbl_height))
        self.R2PPMLineEdit.setReadOnly(True)
        self.R2PPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.Current1LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current1LineEdit.setGeometry(QRect(self.col1x, self.coly*3, self.lbl_width, self.lbl_height))
        self.Current1LineEdit.setReadOnly(True)
        self.Current1LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.N2LineEdit = QLineEdit(parent=self.SetResTab)
        self.N2LineEdit.setGeometry(QRect(self.col1x, self.coly*4, self.lbl_width, self.lbl_height))
        self.N2LineEdit.setReadOnly(True)
        self.N2LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.SHCLineEdit = QLineEdit(parent=self.SetResTab)
        self.SHCLineEdit.setGeometry(QRect(self.col1x, self.coly*5, self.lbl_width, self.lbl_height))
        self.SHCLineEdit.setReadOnly(True)
        self.SHCLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.RampLineEdit = QLineEdit(parent=self.SetResTab)
        self.RampLineEdit.setGeometry(QRect(self.col1x, self.coly*6, self.lbl_width, self.lbl_height))
        self.RampLineEdit.setReadOnly(True)
        self.RampLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # col2
        self.R1ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1ValueLineEdit.setGeometry(QRect(self.col2x, self.coly, self.lbl_width, self.lbl_height))
        self.R1ValueLineEdit.setReadOnly(True)
        self.R1ValueLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R2ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2ValueLineEdit.setGeometry(QRect(self.col2x, self.coly*2, self.lbl_width, self.lbl_height))
        self.R2ValueLineEdit.setReadOnly(True)
        self.R2ValueLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.Current2LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current2LineEdit.setGeometry(QRect(self.col2x, self.coly*3, self.lbl_width, self.lbl_height))
        self.Current2LineEdit.setReadOnly(True)
        self.Current2LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.NAuxLineEdit = QLineEdit(parent=self.SetResTab)
        self.NAuxLineEdit.setGeometry(QRect(self.col2x, self.coly*4, self.lbl_width, self.lbl_height))
        self.NAuxLineEdit.setReadOnly(True)
        self.NAuxLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # self.SampUsedLineEdit.setStyleSheet(
        #         """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.DelayLineEdit = QLineEdit(parent=self.SetResTab)
        self.DelayLineEdit.setGeometry(QRect(self.col2x, self.coly*5, self.lbl_width, self.lbl_height))
        self.DelayLineEdit.setReadOnly(True)
        self.DelayLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.MeasLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasLineEdit.setGeometry(QRect(self.col2x, self.coly*6, self.lbl_width, self.lbl_height))
        self.MeasLineEdit.setReadOnly(True)
        self.MeasLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R1OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1OilPresLineEdit.setGeometry(QRect(self.col2x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1OilPresLineEdit.setReadOnly(True)
        self.R1OilPresLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R2OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2OilPresLineEdit.setGeometry(QRect(self.col2x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2OilPresLineEdit.setReadOnly(True)
        self.R2OilPresLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # col3
        self.kLineEdit = QLineEdit(parent=self.SetResTab)
        self.kLineEdit.setGeometry(QRect(self.col3x, self.coly, self.lbl_width, self.lbl_height))
        self.kLineEdit.setReadOnly(True)
        self.kLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.MeasTimeLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasTimeLineEdit.setGeometry(QRect(self.col3x, self.coly*2, self.lbl_width, self.lbl_height))
        self.MeasTimeLineEdit.setReadOnly(True)
        self.MeasTimeLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.le_deltaI2R2 = QLineEdit(parent=self.SetResTab)
        self.le_deltaI2R2.setGeometry(QRect(self.col3x, self.coly*3, self.lbl_width, self.lbl_height))
        self.le_deltaI2R2.setStyleSheet(
                """QLineEdit { background-color: rgb(255, 255, 255); color: black }""")
        self.le_deltaI2R2.returnPressed.connect(self.changedDeltaI2R2)
        self.R1TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TotalPresLineEdit.setGeometry(QRect(self.col3x, self.coly*4, self.lbl_width, self.lbl_height))
        self.R1TotalPresLineEdit.setReadOnly(True)
        self.R1TotalPresLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R2TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TotalPresLineEdit.setGeometry(QRect(self.col3x, self.coly*5, self.lbl_width, self.lbl_height))
        self.R2TotalPresLineEdit.setReadOnly(True)
        self.R2TotalPresLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.R1TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TempLineEdit.setGeometry(QRect(self.col3x, self.coly*6, self.lbl_width, self.lbl_height))
        self.R1TempLineEdit.returnPressed.connect(self.temp1Changed)
        self.R2TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TempLineEdit.setGeometry(QRect(self.col3x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R2TempLineEdit.returnPressed.connect(self.temp2Changed)
        self.RelHumLineEdit = QLineEdit(parent=self.SetResTab)
        self.RelHumLineEdit.setGeometry(QRect(self.col3x, self.coly*8, self.lbl_width, self.lbl_height))
        self.RelHumLineEdit.setReadOnly(True)
        self.RelHumLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # col4
        self.VMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanLineEdit.setGeometry(QRect(self.col4x, self.coly, self.lbl_width, self.lbl_height))
        self.VMeanLineEdit.setReadOnly(True)
        self.VMeanLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevLineEdit.setGeometry(QRect(self.col4x, self.coly*2, self.lbl_width, self.lbl_height))
        self.StdDevLineEdit.setReadOnly(True)
        self.StdDevLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanLineEdit.setGeometry(QRect(self.col4x, self.coly*3, self.lbl_width, self.lbl_height))
        self.StdDevMeanLineEdit.setReadOnly(True)
        self.StdDevMeanLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.C1LineEdit = QLineEdit(parent=self.SetResTab)
        self.C1LineEdit.setGeometry(QRect(self.col4x, self.coly*4, self.lbl_width, self.lbl_height))
        self.C1LineEdit.setStyleSheet("")
        self.C1LineEdit.setReadOnly(True)
        self.C1LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.C2LineEdit = QLineEdit(parent=self.SetResTab)
        self.C2LineEdit.setGeometry(QRect(self.col4x, self.coly*5, self.lbl_width, self.lbl_height))
        self.C2LineEdit.setStyleSheet("")
        self.C2LineEdit.setReadOnly(True)
        self.C2LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # col5
        self.VMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanChkLineEdit.setGeometry(QRect(self.col5x, self.coly, self.lbl_width, self.lbl_height))
        self.VMeanChkLineEdit.setReadOnly(True)
        self.VMeanChkLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkLineEdit.setGeometry(QRect(self.col5x, self.coly*2, self.lbl_width, self.lbl_height))
        self.StdDevChkLineEdit.setReadOnly(True)
        self.StdDevChkLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanChkLineEdit.setGeometry(QRect(self.col5x, self.coly*3, self.lbl_width, self.lbl_height))
        self.StdDevMeanChkLineEdit.setReadOnly(True)
        self.StdDevMeanChkLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevC1LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC1LineEdit.setGeometry(QRect(self.col5x, self.coly*4, self.lbl_width, self.lbl_height))
        self.StdDevC1LineEdit.setReadOnly(True)
        self.StdDevC1LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevC2LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC2LineEdit.setGeometry(QRect(self.col5x, self.coly*5, self.lbl_width, self.lbl_height))
        self.StdDevC2LineEdit.setReadOnly(True)
        self.StdDevC2LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # col6
        self.R1STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1STPLineEdit.setGeometry(QRect(self.col6x, self.coly, self.lbl_width - 5, self.lbl_height))
        self.R1STPLineEdit.setReadOnly(False)
        self.R1STPLineEdit.setValidator(QDoubleValidator())
        self.R1STPLineEdit.returnPressed.connect(self.changedR1STPPred)
        self.R1STPLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(255, 255, 255); color: black }""")
        self.R2STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2STPLineEdit.setGeometry(QRect(self.col6x, self.coly*2, self.lbl_width - 5, self.lbl_height))
        self.R2STPLineEdit.setReadOnly(False)
        self.R2STPLineEdit.setValidator(QDoubleValidator())
        self.R2STPLineEdit.returnPressed.connect(self.changedR2STPPred)
        self.R2STPLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(255, 255, 255); color: black }""")
        self.NLineEdit = QLineEdit(parent=self.SetResTab)
        self.NLineEdit.setGeometry(QRect(self.col6x, self.coly*3, self.lbl_width- 5, self.lbl_height))
        self.NLineEdit.setReadOnly(True)
        self.NLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevPPMLineEdit.setGeometry(QRect(self.col6x, self.coly*4, self.lbl_width - 5, self.lbl_height))
        self.StdDevPPMLineEdit.setReadOnly(True)
        self.StdDevPPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.StdDevChkPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkPPMLineEdit.setGeometry(QRect(self.col6x, self.coly*5, self.lbl_width - 5, self.lbl_height))
        self.StdDevChkPPMLineEdit.setReadOnly(True)
        self.StdDevChkPPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        # col7
        self.ppmMeanLineEdit = QLineEdit(parent=self.centralwidget)
        self.ppmMeanLineEdit.setGeometry(QRect(self.col7x, self.coly*5, self.lbl_width, self.lbl_height))
        self.ppmMeanLineEdit.setReadOnly(True)
        self.ppmMeanLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        self.RMeanChkPPMLineEdit = QLineEdit(parent=self.centralwidget)
        self.RMeanChkPPMLineEdit.setGeometry(QRect(self.col7x, self.coly*6, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLineEdit.setReadOnly(True)
        self.RMeanChkPPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        self.StdDevMeanPPMLineEdit = QLineEdit(parent=self.centralwidget)
        self.StdDevMeanPPMLineEdit.setGeometry(QRect(self.col7x, self.coly*7, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLineEdit.setReadOnly(True)
        self.StdDevMeanPPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        self.C1C2LineEdit = QLineEdit(parent=self.centralwidget)
        self.C1C2LineEdit.setGeometry(QRect(self.col7x, self.coly*8, self.lbl_width, self.lbl_height))
        self.C1C2LineEdit.setReadOnly(True)
        self.C1C2LineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        self.RatioMeanLineEdit = QLineEdit(parent=self.centralwidget)
        self.RatioMeanLineEdit.setGeometry(QRect(self.col7x, self.coly*9, self.lbl_width, self.lbl_height))
        self.RatioMeanLineEdit.setReadOnly(True)
        self.RatioMeanLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        self.SampUsedLineEdit = QLineEdit(parent=self.centralwidget)
        self.SampUsedLineEdit.setGeometry(QRect(self.col7x, self.coly*10, self.lbl_width, self.lbl_height))
        self.SampUsedLineEdit.setReadOnly(False)
        self.SampUsedLineEdit.returnPressed.connect(self.changedSamplesUsed)

    def BVDTabSetUp(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        global winSizeH
        self.BVDTab = QWidget()
        self.tabWidget.addTab(self.BVDTab, "")
        self.BVDVerticalLayoutWidget = QWidget(parent=self.BVDTab)
        self.BVDVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH-125, 691))
        self.BVDVerticalLayout = QVBoxLayout(self.BVDVerticalLayoutWidget)
        self.BVDfig = plt.figure()
        self.BVDax1 = self.BVDfig.add_subplot(2, 3, (1, 3))
        self.BVDax2 = self.BVDfig.add_subplot(2, 3, (4, 5))
        self.BVDax3 = self.BVDfig.add_subplot(2, 3, 6)
        self.BVDfig.set_tight_layout(True)

        self.BVDax1.tick_params(which='both', direction='in')
        self.BVDax1.set_xlabel('Count')
        self.BVDax1.set_ylabel('Bridge Voltages [V]')
        self.BVDax1.grid(axis='both')

        self.BVDax2.tick_params(which='both', direction='in')
        self.BVDax2.set_xlabel('Count')
        self.BVDax2.tick_params(axis='y', colors='b')
        self.BVDax2.set_axisbelow(True)
        self.BVDax2.grid(axis='x', zorder=0)
        self.BVDax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        box = self.BVDax2.get_position()
        self.BVDax2.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])
        self.BVDtwin2 = self.BVDax2.twinx()
        self.BVDtwin2.tick_params(axis='y', direction='in', colors='r')
        self.BVDtwin2.set_yticklabels([])
        self.BVDtwin2.set_axisbelow(True)
        self.BVDtwin2.grid(zorder=0)

        self.BVDax3.tick_params(which='both', direction='in')
        self.BVDax3.tick_params(axis='y', colors='r')
        self.BVDax3.yaxis.tick_right()
        self.BVDax3.set_ylabel('BVD [V]', color='r')
        self.BVDax3.yaxis.set_label_position('right')
        self.BVDax3.xaxis.set_major_locator(MaxNLocator(integer=True))

        self.BVDcanvas = FigureCanvas(self.BVDfig)
        self.BVDVerticalLayout.addWidget(NavigationToolbar(self.BVDcanvas))
        self.BVDVerticalLayout.addWidget(self.BVDcanvas)

        gridWidget = QWidget(self.BVDTab)
        gridWidget.setGeometry(QRect(0, 690, winSizeH-130, 85))
        grid = QGridLayout(gridWidget)
        grid.setSpacing(5)
        self.deletePlotBut = QPushButton()
        # self.deletePlotBut.setFixedHeight(self.lbl_height)
        self.deletePlotBut.setText('Delete')
        self.deletePlotBut.pressed.connect(self.deleteBut)
        self.plotCountCombo = QComboBox()
        self.RestoreBut = QPushButton()
        # self.RestoreBut.setFixedHeight(self.lbl_height)
        self.RestoreBut.setText('Restore Last')
        self.RestoreBut.pressed.connect(self.restoreDeleted)
        self.RePlotBut = QPushButton()
        # self.RePlotBut.setFixedHeight(self.lbl_height)
        self.RePlotBut.setText('Replot All')
        self.RePlotBut.pressed.connect(self.replotAll)

        SkewnessLabel = QLabel('Skewness', parent=gridWidget)
        KurtosisLabel = QLabel('Kurtosis', parent=gridWidget)
        self.SkewnessEdit = QLineEdit(gridWidget)
        self.SkewnessEdit.setReadOnly(True)
        self.SkewnessEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")
        self.KurtosisEdit = QLineEdit(gridWidget)
        self.KurtosisEdit.setReadOnly(True)
        self.KurtosisEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")
        self.LogoLabelBVD = QLabel(parent=gridWidget)
        self.LogoLabelBVD.setPixmap(self.LogoPixmap)
        self.LogoLabelBVD.setGeometry(QRect(550, 700, 300, 76))
        Spacer1 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        Spacer2 = QSpacerItem(600, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        grid.addWidget(self.deletePlotBut, 1, 1, 2, 1)
        grid.addWidget(self.plotCountCombo, 3, 1, 2, 1)
        grid.addItem(Spacer1, 1, 2)
        grid.addItem(Spacer1, 3, 2)
        grid.addWidget(self.RestoreBut, 1, 3, 2, 1)
        grid.addWidget(self.RePlotBut, 3, 3, 2, 1)
        grid.addItem(Spacer2, 1, 4)
        grid.addItem(Spacer2, 3, 4)
        grid.addWidget(self.LogoLabelBVD, 2, 5, 3, 2)
        grid.addWidget(SkewnessLabel, 1, 7)
        grid.addWidget(self.SkewnessEdit, 2, 7)
        grid.addWidget(KurtosisLabel, 3, 7)
        grid.addWidget(self.KurtosisEdit, 4, 7)

    def AllanTabSetUp(self) -> None:
        """Set up the tab widget for showing allan deviation plots
        Returns
        -------
        None.
        """
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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

        self.Allanax1.set_ylabel('\u03C3(\u03C4), BVD [V]')
        self.Allanax1.set_xlabel('\u03C4 [s]')
        self.Allanax1.set_yscale('log')
        self.Allanax1.set_xscale('log')
        self.Allanax1.grid(which='both')
        # self.Allanax1.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.Allanax1.xaxis.set_major_formatter(ScalarFormatter())

        self.Allanax2.set_ylabel('\u03C3(\u03C4), C1 [V]')
        self.Allanax2.set_xlabel('\u03C4 [s]')
        self.Allanax2.set_yscale('log')
        self.Allanax2.set_xscale('log')
        self.Allanax2.grid(which='both')
        # self.Allanax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.Allanax2.xaxis.set_major_formatter(ScalarFormatter())

        self.Allanax3.set_ylabel('\u03C3(\u03C4), C2 [V]')
        self.Allanax3.set_xlabel('\u03C4 [s]')
        self.Allanax3.set_yscale('log')
        self.Allanax3.set_xscale('log')
        self.Allanax3.grid(which='both')
        # self.Allanax3.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.Allanax3.xaxis.set_major_formatter(ScalarFormatter())

        self.Allanax4.set_ylabel('\u03C3(\u03C4), BV [V]')
        self.Allanax4.set_xlabel('\u03C4 [s]')
        self.Allanax4.set_yscale('log')
        self.Allanax4.set_xscale('log')
        self.Allanax4.grid(which='both')
        # self.Allanax4.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.Allanax4.xaxis.set_major_formatter(ScalarFormatter())

        self.AllanCanvas = FigureCanvas(self.Allanfig)
        self.AllanVerticalLayout.addWidget(NavigationToolbar(self.AllanCanvas))
        self.AllanVerticalLayout.addWidget(self.AllanCanvas)

        self.AllanHorizontalLayout = QHBoxLayout()
        self.AllanTypeComboBox = QComboBox(parent=self.AllanTab)
        self.AllanTypeComboBox.setEditable(False)
        self.AllanTypeComboBox.addItem('all')
        self.AllanTypeComboBox.addItem('2^n (octave)')
        self.AllanTypeComboBox.currentIndexChanged.connect(self.plotAdev)

        self.OverlappingComboBox = QComboBox(parent=self.AllanTab)
        self.OverlappingComboBox.setEditable(False)
        self.OverlappingComboBox.addItem('non-overlapping')
        self.OverlappingComboBox.addItem('overlapping')
        self.OverlappingComboBox.currentIndexChanged.connect(self.plotAdev)
        self.AllanHorizontalSpacer = QSpacerItem(600, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.LogoLabelAllan = QLabel(parent=self.AllanTab)
        self.LogoLabelAllan.setPixmap(self.LogoPixmap)
        self.LogoLabelAllan.setGeometry(QRect(550, 700, 300, 76))

        self.AllanHorizontalLayout.addWidget(self.AllanTypeComboBox)
        self.AllanHorizontalLayout.addItem(self.AllanHorizontalSpacer)
        self.AllanHorizontalLayout.addWidget(self.LogoLabelAllan)
        self.AllanHorizontalLayout.addWidget(self.OverlappingComboBox)
        self.AllanVerticalLayout.addLayout(self.AllanHorizontalLayout)

    def SpecTabSetUp(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        global winSizeH
        self.SpecTab = QWidget()
        self.tabWidget.addTab(self.SpecTab, "")
        self.SpecVerticalLayoutWidget = QWidget(parent=self.SpecTab)
        self.SpecVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH - 125, 675))
        self.SpecVerticalLayout = QVBoxLayout(self.SpecVerticalLayoutWidget)

        self.Specfig = plt.figure()
        self.SpecAx = self.Specfig.add_subplot(2,2,1)
        self.SpecAx.tick_params(axis='both', which='both', direction='in')
        self.SpecAx.set_ylabel('PSD of BVD [$V^2$/' + 'Hz' + ']')
        self.SpecAx.set_xlabel('Frequency [Hz]')
        self.SpecAx.grid(which='both')
        self.SpecAx.set_yscale('log')
        self.SpecAx.set_xscale('log')

        self.specAB = self.Specfig.add_subplot(2,2,2)
        self.specAB.tick_params(axis='both', which='both', direction='in')
        self.specAB.set_ylabel('PSD of BV [$V^2$/' + 'Hz' + ']')
        self.specAB.set_xlabel('Frequency [Hz]')
        self.specAB.grid(which='both')
        self.specAB.set_yscale('log')
        self.specAB.set_xscale('log')
        
        self.acf_bvd = self.Specfig.add_subplot(2,2,3)
        self.acf_bvd.tick_params(axis='both', which='both', direction='in')
        self.acf_bvd.set_ylabel('ACF of BVD')
        self.acf_bvd.set_xlabel('lag')
        self.acf_bvd.grid(which='both')
        
        self.acf_bv = self.Specfig.add_subplot(2,2,4)
        self.acf_bv.tick_params(axis='both', which='both', direction='in')
        self.acf_bv.set_ylabel('ACF of BV')
        self.acf_bv.set_xlabel('lag')
        self.acf_bv.grid(which='both')
        
        self.Specfig.set_tight_layout(True)
        self.SpecCanvas = FigureCanvas(self.Specfig)
        
        self.SpecVerticalLayout.addWidget(NavigationToolbar(self.SpecCanvas))
        self.SpecVerticalLayout.addWidget(self.SpecCanvas)
        
        gridWidget = QWidget(self.SpecTab)
        gridWidget.setGeometry(QRect(0, 675, winSizeH-125, 90))
        QRect()
        grid = QGridLayout(gridWidget)
        grid.setSpacing(5)

        lbl_lag_bvd = QLabel('Lag of BVD', parent=gridWidget)
        self.le_lag_bvd = QLineEdit(gridWidget)
        self.le_lag_bvd.setReadOnly(True)
        self.le_lag_bvd.setFixedWidth(100)
        self.le_lag_bvd.setFixedHeight(18)
        self.le_lag_bvd.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_alpha_bvd = QLabel('Alpha [BVD]', parent=gridWidget)
        self.le_alpha_bvd= QLineEdit(gridWidget)
        self.le_alpha_bvd.setReadOnly(True)
        self.le_alpha_bvd.setFixedWidth(130)
        self.le_alpha_bvd.setFixedHeight(18)
        self.le_alpha_bvd.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_lag_bva = QLabel('Lag of A', parent=gridWidget)
        self.le_lag_bva = QLineEdit(gridWidget)
        self.le_lag_bva.setReadOnly(True)
        self.le_lag_bva.setFixedWidth(100)
        self.le_lag_bva.setFixedHeight(18)
        self.le_lag_bva.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_alpha_bva = QLabel('Alpha [A]', parent=gridWidget)
        self.le_alpha_bva= QLineEdit(gridWidget)
        self.le_alpha_bva.setReadOnly(True)
        self.le_alpha_bva.setFixedWidth(130)
        self.le_alpha_bva.setFixedHeight(18)
        self.le_alpha_bva.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_lag_bvb = QLabel('Lag of B', parent=gridWidget)
        self.le_lag_bvb = QLineEdit(gridWidget)
        self.le_lag_bvb.setReadOnly(True)
        self.le_lag_bvb.setFixedWidth(100)
        self.le_lag_bvb.setFixedHeight(18)
        self.le_lag_bvb.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_alpha_bvb = QLabel('Alpha [B]', parent=gridWidget)
        self.le_alpha_bvb= QLineEdit(gridWidget)
        self.le_alpha_bvb.setReadOnly(True)
        self.le_alpha_bvb.setFixedWidth(130)
        self.le_alpha_bvb.setFixedHeight(18)
        self.le_alpha_bvb.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")
        # Spacer1 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        # Spacer2 = QSpacerItem(600, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        grid.addWidget(lbl_lag_bvd, 1, 1, 1, 1)
        grid.addWidget(self.le_lag_bvd, 3, 1, 1, 1)
        
        grid.addWidget(lbl_lag_bva, 1, 2, 1, 1)
        grid.addWidget(self.le_lag_bva, 3, 2, 1, 1)
        
        grid.addWidget(lbl_lag_bvb, 1, 3, 1, 1)
        grid.addWidget(self.le_lag_bvb, 3, 3, 1, 1)
        
        grid.addWidget (lbl_alpha_bvd, 5, 1, 1, 1)
        grid.addWidget(self.le_alpha_bvd, 7, 1, 1, 1)

        grid.addWidget (lbl_alpha_bva, 5, 2, 1, 1)
        grid.addWidget(self.le_alpha_bva, 7, 2, 1, 1)
        
        grid.addWidget (lbl_alpha_bvb, 5, 3, 1, 1)
        grid.addWidget(self.le_alpha_bvb, 7, 3, 1, 1)

    def setButtons(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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
        self.CurrentBut.setStyleSheet(blue_style)
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
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.R1OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R1OilDepthSpinBox.setGeometry(QRect(self.col1x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1OilDepthSpinBox.setMaximum(1000)
        self.R1OilDepthSpinBox.valueChanged.connect(self.oilDepth1Changed)
        self.R2OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R2OilDepthSpinBox.setGeometry(QRect(self.col1x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2OilDepthSpinBox.setMaximum(1000)
        self.R2OilDepthSpinBox.valueChanged.connect(self.oilDepth2Changed)

    def setComboBoxes(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        _translate = QCoreApplication.translate
        mainWindow.setWindowTitle(_translate("mainWindow", "Magnicon Offline Analyzer " + str(__version__) ))
        self.R1OilDepthLabel.setText(_translate("mainWindow", "R<sub>1</sub> Oil Depth [mm]"))
        self.RelHumLabel.setText(_translate("mainWindow", "Rel. Humidity [%]"))
        self.R2TempLabel.setText(_translate("mainWindow", f'R<sub>2</sub> Temperature [{chr(176)}C]'))
        self.R1PresLabel.setText(_translate("mainWindow", "R<sub>1</sub> Pressure [Pa]"))
        self.MagElecLabel.setText(_translate("mainWindow", "Magnicon Electronics"))
        self.R1OilPresLabel.setText(_translate("mainWindow", "R<sub>1</sub> Oil Pressure [Pa]"))
        self.R2OilPresLabel.setText(_translate("mainWindow", "R<sub>2</sub> Oil Pressure [Pa]"))
        self.R1TempLabel.setText(_translate("mainWindow", f'R<sub>1</sub> Temperature [{chr(176)}C]'))
        self.StandardRLabel.setText(_translate("mainWindow", "Standard R"))
        self.MeasTimeLabel.setText(_translate("mainWindow", "Measurement Time"))
        self.lbl_deltaI2R2.setText(_translate("mainWindow", f"{chr(916)}(I<sub>2</sub>R<sub>2</sub>) [V]"))
        self.kLabel.setText(_translate("mainWindow", "k [mTurns]"))
        self.SquidFeedLabel.setText(_translate("mainWindow", "SQUID Feedin Polarity"))
        self.StandardRBut.setText(_translate("mainWindow", self.RButStatus))
        self.R1TotalPresLabel.setText(_translate("mainWindow", "R<sub>1</sub> Total Pres. [Pa]"))
        self.VMeanLabel.setText(_translate("mainWindow", "Mean [V]"))
        self.RMeanChkPPMLabel.setText(_translate("mainWindow", f"R Mean Chk [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.C2Label.setText(_translate("mainWindow", f"C<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevMeanLabel.setText(_translate("mainWindow", "Std. Mean"))
        self.R1STPLabel.setText(_translate("mainWindow", f"R1STPPred [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.R2STPLabel.setText(_translate("mainWindow", f"R2STPPred [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.C1Label.setText(_translate("mainWindow", f"C<sub>1</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevC2Label.setText(_translate("mainWindow", f"Std Dev C<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevC1Label.setText(_translate("mainWindow", f"Std Dev C<sub>1</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.RatioMeanLabel.setText(_translate("mainWindow", "Ratio Mean"))
        self.ppmMeanLabel.setText(_translate("mainWindow", f"Mean [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.C1C2Label.setText(_translate("mainWindow", f"C<sub>1</sub>-C<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevMeanPPMLabel.setText(_translate("mainWindow", f"Std. Mean [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevLabel.setText(_translate("mainWindow", "Std. Dev."))
        self.StdDevPPMLabel.setText(_translate("mainWindow", f"Std. Dev. [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.NLabel.setText(_translate("mainWindow", "N"))
        self.StdDevChkPPMLabel.setText(_translate("mainWindow", f"Std. Dev. Chk [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.NAuxLabel.setText(_translate("mainWindow", "NAux [Turns]"))
        self.SHCLabel.setText(_translate("mainWindow", "Sample Half Cycle"))
        self.N2Label.setText(_translate("mainWindow", "N<sub>2</sub> [Turns]"))
        self.R2ValueLabel.setText(_translate("mainWindow", f"R<sub>2</sub> Value [{chr(937)}]"))
        self.N1Label.setText(_translate("mainWindow", "N<sub>1</sub> [Turns]"))
        self.Current1Label.setText(_translate("mainWindow", "I<sub>1</sub> [A]"))
        self.FullCycLabel.setText(_translate("mainWindow", "Full Cycle [s]"))
        self.Current2Label.setText(_translate("mainWindow", "I<sub>2</sub> [A]"))
        self.MeasCycLabel.setText(_translate("mainWindow", "Meas. Cycles"))
        self.R1SNLabel.setText(_translate("mainWindow", "R<sub>1</sub> Serial Number"))
        self.R2SNLabel.setText(_translate("mainWindow", "R<sub>2</sub> Serial Number"))
        self.RampLabel.setText(_translate("mainWindow", "Ramp [s]"))
        self.R1PPMLabel.setText(_translate("mainWindow", f'R<sub>1</sub> [{chr(956)}{chr(937)}/{chr(937)}]'))
        self.R2PPMLabel.setText(_translate("mainWindow", f'R<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]'))
        self.R1ValueLabel.setText(_translate("mainWindow", f"R<sub>1</sub> Value [{chr(937)}]"))
        self.AppVoltLabel.setText(_translate("mainWindow", "Applied Voltage"))
        self.MeasLabel.setText(_translate("mainWindow", "Meas [s]"))
        self.DelayLabel.setText(_translate("mainWindow", "Delay [s]"))
        self.SampUsedLabel.setText(_translate("mainWindow", "Samples Used"))
        self.ResultsLabel.setText(_translate("mainWindow", "RESULTS"))
        self.lbl_ccceq.setText(_translate("mainWindow", "CCC EQUATION"))
        self.SquidFeedBut.setText(_translate("mainWindow", "Negative"))
        self.SettingsLabel.setText(_translate("mainWindow", "SETTINGS"))
        self.CommentsLabel.setText(_translate("mainWindow", "Comments"))
        self.R2TotalPresLabel.setText(_translate("mainWindow", "R<sub>2</sub> Total Pres. [Pa]"))
        self.R2PresLabel.setText(_translate("mainWindow", "R<sub>2</sub> Pressure [Pa]"))
        self.R2OilDepthLabel.setText(_translate("mainWindow", "R<sub>2</sub> Oil Depth [mm]"))
        self.ProbeLabel.setText(_translate("mainWindow", "Probe"))
        self.CurrentButLabel.setText(_translate("mainWindow", "SQUID Feedin Arm"))
        self.CurrentBut.setText(_translate("mainWindow", self.CurrentButStatus))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.BVDTab), _translate("mainWindow", "BVD"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.AllanTab), _translate("mainWindow", "Allan Dev."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SpecTab), _translate("mainWindow", "Power Spec."))
        self.txtFileLabel.setText(_translate("mainWindow", ".txt file"))
        self.VMeanChkLabel.setText(_translate("mainWindow", "Mean Chk [V]"))
        self.StdDevChkLabel.setText(_translate("mainWindow", "Std. Dev. Chk"))
        self.StdDevMeanChkLabel.setText(_translate("mainWindow", "Std. Mean Chk"))
        self.saveButton.setText(_translate("mainWindow", "Save"))
        self.MDSSButton.setText(_translate("mainWindow", "No"))
        self.MDSSLabel.setText(_translate("mainWindow", "Save MDSS"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))

    def plotBVD(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.bvd_stat_obj is not None:
            count = linspace(0, len(self.A)-1, num=len(self.A))
            if self.bvdList:
                BVDmean = mean(self.bvdList)
                BVDstd  = std(self.bvdList, ddof=1)
                upper   =  3*BVDstd + BVDmean
                lower   = -3*BVDstd + BVDmean
                if self.plottedBVD:
                    self.clearBVDPlot()
                    self.BVDax1_ref[0].set_data(count, self.A)
                    self.BVDax12_ref[0].set_data(count, self.B)
                    if self.RButStatus == 'R1':
                        self.BVDax21_ref[0].set_data(self.bvdCount, self.R1List)
                    else:
                        self.BVDax21_ref[0].set_data(self.bvdCount, self.R2List)
                    self.BVDtwin21_ref[0].set_data(self.bvdCount, self.bvdList)
                    self.BVDtwin22_ref[0].set_data(self.bvdCount, upper*ones(len(self.bvdList), dtype=int))
                    self.BVDtwin23_ref[0].set_data(self.bvdCount, lower*ones(len(self.bvdList), dtype=int))
                    self.BVDax3.hist(self.bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                    self.BVDax3.set_ylim([self.BVDtwin2.get_ylim()[0], self.BVDtwin2.get_ylim()[1]])
                else:
                    # plot the individual bridge voltages
                    self.BVDax1_ref = self.BVDax1.errorbar(count, self.A, marker='o', ms=6, mfc='red', mec='red', ls='', alpha=self.alpha, label='I+')
                    self.BVDax12_ref = self.BVDax1.errorbar(count, self.B, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label='I-')
                    self.BVDax1.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', frameon=True, shadow=True, ncols=2, columnspacing=0)

                    if self.RButStatus == 'R1':
                        self.BVDax21_ref = self.BVDax2.plot(self.bvdCount, self.R1List, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label= 'Resistance')
                    else:
                        self.BVDax21_ref = self.BVDax2.plot(self.bvdCount, self.R2List, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label= 'Resistance')
                    self.BVDtwin21_ref = self.BVDtwin2.plot(self.bvdCount, self.bvdList, marker='o', ms=6, mfc='red', mec='red', ls='', alpha=self.alpha, label= 'BVD [V]')
                    self.BVDtwin22_ref = self.BVDtwin2.plot(self.bvdCount, upper*ones(len(self.bvdList), dtype=int), marker='', color='red', ms=0, ls='--', alpha=self.alpha)
                    self.BVDtwin23_ref = self.BVDtwin2.plot(self.bvdCount, lower*ones(len(self.bvdList), dtype=int), marker='', color='red', ms=0, ls='--', alpha=self.alpha)

                    self.BVDax3.hist(self.bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                    self.BVDax3.set_ylim([self.BVDtwin2.get_ylim()[0], self.BVDtwin2.get_ylim()[1]])
                # Put a legend below current axis
                lines, labels   = self.BVDax2.get_legend_handles_labels()
                lines2, labels2 = self.BVDtwin2.get_legend_handles_labels()
                self.BVDax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.2),
                                   fancybox=True, shadow=True, ncols=2, columnspacing=0)
                if self.RButStatus == 'R1':
                    self.BVDax2.set_ylabel(f'R2 [{chr(956)}{chr(937)}/{chr(937)}]', color='b')
                else:
                    self.BVDax2.set_ylabel(f'R1 [{chr(956)}{chr(937)}/{chr(937)}]', color='b')

                self.BVDax1.relim()
                self.BVDax1.autoscale(tight=None, axis='both', enable=True)
                self.BVDax1.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDax2.relim()
                self.BVDax2.autoscale(tight=None, axis='both', enable=True)
                self.BVDax2.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDtwin2.relim()
                self.BVDtwin2.autoscale(tight=None, axis='both', enable=True)
                self.BVDtwin2.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDax3.set_ylim([self.BVDtwin2.get_ylim()[0], self.BVDtwin2.get_ylim()[1]])
                self.BVDax3.relim()
                self.BVDax3.autoscale(tight=None, axis='both', enable=True)
                self.BVDax3.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDcanvas.draw()
                self.BVDcanvas.flush_events()
                self.BVDfig.set_tight_layout(True)
                self.SkewnessEdit.setText(str("{:.3f}".format(mystat.skewness(self.bvdList))))
                self.KurtosisEdit.setText(str("{:.3f}".format(mystat.kurtosis(self.bvdList))))
                self.plottedBVD = True
                
                
    def changedR1STPPred(self,):
        self.changedR1STPBool = True
        self.R1STP = float(self.R1STPLineEdit.text())
        self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        self.setValidData()
        self.plotBVD()

    def changedR2STPPred(self,):
        self.changedR2STPBool = True
        self.R2STP = float(self.R2STPLineEdit.text())
        self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        self.setValidData()
        self.plotBVD()
        return

    def changedDeltaI2R2(self, ):
        if float(self.le_deltaI2R2.text()) != 0.0:
            self.cleanUp()
            self.changedDeltaI2R2Ct = 1
            self.getBVD()
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()

    def changedSamplesUsed(self, ):
        if int(self.SampUsedLineEdit.text()) != 0 and int(self.SampUsedLineEdit.text()) <= int(self.dat.SHC) and int(self.SampUsedLineEdit.text())%2 == 0:
            self.cleanUp()
            self.SampUsedCt = 1
            self.getBVD()
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()
            self.plotStatMeasures()

    def is_overlapping(self, overlapping: str) -> bool:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if overlapping == 'overlapping':
            return True
        else:
            return False

    def powers_of_2(self, n: int) -> list:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        x   = 1
        arr = []
        while(x < n):
            arr.append(x)
            x = x*2
        return arr

    def plotAllan(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.bvdList:
            if self.AllanTypeComboBox.currentText() == '2^n (octave)':
                tau_list = self.powers_of_2(int(len(self.bvdList)//2))
                mytaus = 'octave'
            elif self.AllanTypeComboBox.currentText() == 'all':
                tau_list = list(map(int, linspace(1, len(self.bvdList)//2, len(self.bvdList)//2)))
                mytaus = 'all'
            # tau list is same for all...
            tau_list_C1 = tau_list
            tau_list_C2 = tau_list
            tau_list_bva = tau_list
            tau_list_bvb = tau_list
            # bvd_tau, bvd_adev_ali, bvd_aerr = mystat.adev(array(self.bvdList), self.overlapping, tau_list)
            # C1_tau, C1_adev, C1_aerr = mystat.adev(array(self.V1), self.overlapping, tau_list_C1)
            # C2_tau, C2_adev, C2_aerr = mystat.adev(array(self.V2), self.overlapping, tau_list_C2)
            # bva_tau, bva_adev, bva_aerr = mystat.adev(array(self.A), self.overlapping, tau_list_bva)
            # bvb_tau, bvb_adev, bvb_aerr = mystat.adev(array(self.B), self.overlapping, tau_list_bvb)
            # using allantools because it is faster than O(n^2)
            if self.overlapping:
                (bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn) = allantools.oadev(array(self.bvdList), rate=1/self.dat.fullCyc, data_type="freq", taus=mytaus)
                (C1_tau, C1_adev, C1_aerr, C1_adn) = allantools.oadev(array(self.V1), rate=1/self.dat.fullCyc, data_type="freq", taus=mytaus)
                (C2_tau, C2_adev, C2_aerr, C2_adn) = allantools.oadev(array(self.V2), rate=1/self.dat.fullCyc, data_type="freq", taus=mytaus)
                (bva_tau_time, bva_adev, bva_aerr, bva_adn) = allantools.oadev(array(self.A), rate=1/self.dat.dt, data_type="freq", taus=mytaus)
                (bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn) = allantools.oadev(array(self.B), rate=1/self.dat.dt, data_type="freq", taus=mytaus)
            else:
                (bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn) = allantools.adev(array(self.bvdList), rate=1/self.dat.fullCyc, data_type="freq", taus=mytaus)  # Compute the overlapping ADEV
                (C1_tau, C1_adev, C1_aerr, C1_adn) = allantools.adev(array(self.V1), rate=1/self.dat.fullCyc, data_type="freq", taus=mytaus)
                (C2_tau, C2_adev, C2_aerr, C2_adn) = allantools.adev(array(self.V2), rate=1/self.dat.fullCyc, data_type="freq", taus=mytaus)
                (bva_tau_time, bva_adev, bva_aerr, bva_adn) = allantools.adev(array(self.A), rate=1/self.dat.dt, data_type="freq", taus=mytaus)
                (bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn) = allantools.adev(array(self.B), rate=1/self.dat.dt, data_type="freq", taus=mytaus)

            rttau = []
            # bvd_tau_time = []
            # for i in bvd_tau:
            #     bvd_tau_time_ali.append(i*self.dat.fullCyc)
            #     rttau.append(sqrt(self.h0)*sqrt(1/(2*i*self.dat.fullCyc)))

            # for i in bva_tau:
            #     bva_tau_time.append(i*self.dat.dt)
            # print(rttau, bvd_tau)

            for i in bvd_tau_time:
                rttau.append(sqrt(self.h0)*sqrt(1/(2*i)))
            # print(rttau[0])

            if self.plottedAllan:
                self.clearAllanPlot()
                self.Allanax1_ref[0].set_data(array(bvd_tau_time), array(bvd_adev))
                self.Allanax11_ref[0].set_data(array(bvd_tau_time), array(rttau))
                self.Allanax2_ref[0].set_data(array(bvd_tau_time), array(C1_adev))
                self.Allanax3_ref[0].set_data(array(bvd_tau_time), array(C2_adev))
                self.Allanax41_ref[0].set_data(array(bva_tau_time), array(bva_adev))
                self.Allanax42_ref[0].set_data(array(bva_tau_time), array(bvb_adev))
            else:
                self.Allanax1_ref = self.Allanax1.plot(bvd_tau_time, bvd_adev, 'ko-', lw=1.25, ms=4, alpha = self.alpha) # ADev for BVD
                self.Allanax11_ref = self.Allanax1.plot(bvd_tau_time,  rttau, 'r', lw = 2, alpha=self.alpha-0.1, label=r'$1/\sqrt{\tau}$')
                self.Allanax2_ref = self.Allanax2.plot(bvd_tau_time, C1_adev, 'bo-', lw=1.25, ms=4, alpha = self.alpha) # ADev for C1
                self.Allanax3_ref = self.Allanax3.plot(bvd_tau_time, C2_adev, 'bo-', lw=1.25, ms=4, alpha=self.alpha) # ADev for C2
                self.Allanax41_ref = self.Allanax4.plot(bva_tau_time, bva_adev, 'ro-', lw=1.25, ms=4, alpha=self.alpha, label='I+') # ADev for bv a
                self.Allanax42_ref = self.Allanax4.plot(bva_tau_time, bvb_adev, 'bo-', lw=1.25, ms=4, alpha=self.alpha, label='I-') # ADev for bv b
                self.plottedAllan = True
        self.Allanax1.legend(loc='upper right', frameon=True, shadow=True, ncols=1, columnspacing=0)
        self.Allanax1.relim()
        self.Allanax1.autoscale(tight=None, axis='both', enable=True)
        self.Allanax1.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax2.relim()
        self.Allanax2.autoscale(tight=None, axis='both', enable=True)
        self.Allanax2.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax3.relim()
        self.Allanax3.autoscale(tight=None, axis='both', enable=True)
        self.Allanax3.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax4.legend(loc='lower left', frameon=True, shadow=True, ncols=2, columnspacing=1)
        self.Allanax4.relim()
        self.Allanax4.autoscale(tight=None, axis='both', enable=True)
        self.Allanax4.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanfig.set_tight_layout(True)
        self.AllanCanvas.draw()
        
        with open(self.pathString + '_pyadev.txt', 'w') as adev_file:
            # Create header string
            adev_file.write('tau (s)' + '\t' + 'adev [BVD]' + '\t' + 'adev err [BVD]' + \
                            '\n')
        with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
            for i, j, k, in zip(bvd_tau_time, bvd_adev, bvd_aerr):
                adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
            adev_file.write('\n')

        with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
            adev_file.write('tau (s)' + '\t' + 'adev [BV A]' + '\t' + 'adev err [BV A]' + \
                            '\n')
        with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
            for i, j, k, in zip(bva_tau_time, bva_adev, bva_aerr):
                adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
            adev_file.write('\n')
        
        with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
            adev_file.write('tau (s)' + '\t' + 'adev [BV B]' + '\t' + 'adev err [BV B]' + \
                            '\n')
        with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
            for i, j, k, in zip(bvb_tau_time, bvb_adev, bvb_aerr):
                adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
            adev_file.write('\n')

    def plotSpec(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        samp_freq = 1./(self.dat.fullCyc)
        # sig_freq = 1./(self.dat.fullCyc)
        print("BVD Sampling frequency: ", samp_freq)
        print("Measurement time: ", self.dat.measTime)
        print("BV Sampling frequency: ", self.dat.dt)
        # Create the window function
        freq_bvd, mypsd_bvd = signal.welch(array(self.bvdList), fs=samp_freq, window='hann', \
                                         nperseg=len(self.bvdList), scaling='density', \
                                         axis=-1, average='mean', return_onesided=True)
        freqA, mypsdA = signal.welch(array(self.A), fs=self.dat.dt, window='hann', \
                                         nperseg=len(self.A),  scaling='density', \
                                         axis=-1, average='mean', return_onesided=True)
        freqB, mypsdB = signal.welch(array(self.B), fs=self.dat.dt, window='hann', \
                                         nperseg=len(self.B),  scaling='density', \
                                         axis=-1, average='mean', return_onesided=True)
        self.h0 = mean(mypsd_bvd[1:])
        print("Noise power BVD: ", mean(mypsd_bvd[1:]))
        print("Noise power BVA: ", mean(mypsdA[1:]))
        print("Noise power BVB: ", mean(mypsdB[1:]))

        # Ali's custom PSD calculation...[works but slower than scipy welch]
        # mywindow_mystat = mystat.hann(float(samp_freq), (len(self.bvdList)*float(samp_freq)))
        # freq_bvd, mypsa_bvd = mystat.calc_fft(1./(float(samp_freq)), array(self.bvdList), array(mywindow_mystat))
        lag_bvd, acf_bvd, pci_bvd, nci_bvd, cutoff_lag_bvd = mystat.autoCorrelation(array(self.bvdList))
        lag_bva, acf_bva, pci_bva, nci_bva, cutoff_lag_bva = mystat.autoCorrelation(array(self.A))
        lag_bvb, acf_bvb, pci_bvb, nci_bvb, cutoff_lag_bvb = mystat.autoCorrelation(array(self.B))
        (pow_bvd, noise_bvd) = mystat.noise1D(array(self.bvdList))
        (pow_bva, noise_bva) = mystat.noise1D(array(self.A))
        (pow_bvb, noise_bvb) = mystat.noise1D(array(self.B))
        
        if self.plottedSpec:
            self.clearSpecPlot()
            self.SpecAx_ref[0].set_data(array(freq_bvd), array(mypsd_bvd))
            self.SpecAx_ref1[0].set_data(array(freq_bvd), mean(mypsd_bvd[1:])*ones(len(freq_bvd)))
            self.specA_ref[0].set_data(array(freqA), array(mypsdA))
            self.specB_ref[0].set_data(array(freqB), array(mypsdB))
            self.acf_bvd_ref[0].set_data(array(lag_bvd[0:]), array(acf_bvd[0:]))
            self.acf_bvd_ref1[0].set_data(array(lag_bvd[0:]), array(pci_bvd[0:]))
            self.acf_bvd_ref2[0].set_data(array(lag_bvd[0:]), array(nci_bvd[0:]))
            self.acf_bv_refa[0].set_data(array(lag_bva), array(acf_bva))
            self.acf_bv_refb[0].set_data(array(lag_bvb), array(acf_bvb))
        else:
            # PSD of BVD
            self.SpecAx_ref = self.SpecAx.plot(freq_bvd, mypsd_bvd, 'ko-', lw=1.25, ms=2, alpha=self.alpha)
            self.SpecAx_ref1 = self.SpecAx.plot(freq_bvd, mean(mypsd_bvd[1:])*ones(len(freq_bvd)), 'r', lw=2, alpha=self.alpha-0.1, label=r'$h_0$')
            # PSD of BVA and BVB
            self.specA_ref = self.specAB.plot(freqA, mypsdA, 'ro-', lw=1.25, ms=2, alpha=self.alpha, label='I+')
            self.specB_ref = self.specAB.plot(freqB, mypsdB, 'bo-', lw=1.25, ms=2, alpha=self.alpha, label='I-')
            # ACF of BVD
            self.acf_bvd_ref = self.acf_bvd.plot(lag_bvd[0:], acf_bvd[0:], 'ko-', lw=0.5, ms = 4, alpha=self.alpha)
            self.acf_bvd_ref1 = self.acf_bvd.plot(lag_bvd[0:], pci_bvd[0:], ':', lw=2, color='red')
            self.acf_bvd_ref2 = self.acf_bvd.plot(lag_bvd[0:], nci_bvd[0:], ':', lw=2, color='red')
            # ACF of BVA and BVB
            self.acf_bv_refa = self.acf_bv.plot(lag_bva[0:], acf_bva[0:], 'ro', ms=2, alpha=self.alpha, label='I+')
            self.acf_bv_refb = self.acf_bv.plot(lag_bvb[0:], acf_bvb[0:], 'bo', ms=2, alpha=self.alpha, label='I-')
            
            # print(acf_bvd[0:]+ pci_bvd[0:])
            # self.autoCorr_ref1 = self.autoCorr.fill_between(lag_bvd[0:], acf_bvd[0:]+pci_bvd[0:], acf_bvd[0:]-nci_bvd[0:], lw=2, facecolor='red')
            self.plottedSpec = True
        self.SpecAx.legend(loc='lower left', frameon=True, shadow=True, ncols=1, columnspacing=0)
        self.SpecAx.relim()
        self.SpecAx.autoscale(tight=None, axis='both', enable=True)
        self.SpecAx.autoscale_view(tight=None, scalex=True, scaley=True)
        self.specAB.legend(loc='lower left', frameon=True, shadow=True, ncols=1, columnspacing=0)
        self.specAB.relim()
        self.specAB.autoscale(tight=None, axis='both', enable=True)
        self.specAB.autoscale_view(tight=None, scalex=True, scaley=True)
        self.acf_bvd.relim()
        self.acf_bvd.autoscale(tight=None, axis='both', enable=True)
        self.acf_bvd.autoscale_view(tight=None, scalex=True, scaley=True)
        self.acf_bv.legend(loc='upper right', frameon=True, shadow=True, ncols=1, columnspacing=0)
        self.acf_bv.relim()
        self.acf_bv.autoscale(tight=None, axis='both', enable=True)
        self.acf_bv.autoscale_view(tight=None, scalex=True, scaley=True)
        
        self.le_lag_bvd.setText(str(cutoff_lag_bvd))
        self.le_alpha_bvd.setText(str(pow_bvd) + ': ' + noise_bvd)
        self.le_lag_bva.setText(str(cutoff_lag_bva))
        self.le_alpha_bva.setText(str(pow_bva) + ': ' + noise_bva)
        self.le_lag_bvb.setText(str(cutoff_lag_bvb))
        self.le_alpha_bvb.setText(str(pow_bvb) + ': ' + noise_bvb)
        
        self.Specfig.set_tight_layout(True)
        self.SpecCanvas.draw()
        
        with open(self.pathString + '_pypsd.txt', 'w') as psd_file:
            # Create header string
            psd_file.write('f (Hz)' + '\t' + 'psd [BVD]' + '\n')
        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            for i, j, in zip(freq_bvd, mypsd_bvd):
                psd_file.write(str(i) + '\t' + str(j) + '\n')
            psd_file.write('\n')

        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            psd_file.write('f (Hz)' + '\t' + 'psd [BV A]' + '\n')
        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            for i, j, in zip(freqA, mypsdA):
                psd_file.write(str(i) + '\t' + str(j) + '\n')
            psd_file.write('\n')
        
        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            psd_file.write('f (Hz)' + '\t' + 'psd [BV B]' + '\n')
        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            for i, j, in zip(freqB, mypsdB):
                psd_file.write(str(i) + '\t' + str(j) + '\n')
            psd_file.write('\n')

    def clearBVDPlot(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.plottedBVD:
            try:
                # print("Trying to clear BVD Plots")
                self.BVDax1_ref[0].set_data(array([]), array([]))
                self.BVDax12_ref[0].set_data(array([]), array([]))
                self.BVDax21_ref[0].set_data(array([]), array([]))
                self.BVDtwin21_ref[0].set_data(array([]), array([]))
                self.BVDtwin22_ref[0].set_data(array([]), array([]))
                self.BVDtwin23_ref[0].set_data(array([]), array([]))
                for container in self.BVDax3.containers:
                    container.remove()
                # self.BVDax1.clear()
                # self.BVDax2.clear()
                # self.BVDtwin2.clear()
                # self.BVDax3.clear()
            except Exception as e:
                print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
                pass

    def clearAllanPlot(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.plottedAllan:
            try:
                 # print("Trying to clear Allan Plots")
                 self.Allanax1_ref[0].set_data(array([]), array([]))
                 self.Allanax11_ref[0].set_data(array([]), array([]))
                 self.Allanax2_ref[0].set_data(array([]), array([]))
                 self.Allanax3_ref[0].set_data(array([]), array([]))
                 self.Allanax41_ref[0].set_data(array([]), array([]))
                 self.Allanax42_ref[0].set_data(array([]), array([]))
                 
                 # self.Allanax1.clear()
                 # self.Allanax2.clear()
                 # self.Allanax3.clear()
                 # self.Allanax4.clear()

            except Exception as e:
                  print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
                  pass

    def clearSpecPlot(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.plottedSpec:
            try:
                # print("Trying to clear Spectrum Plots")
                self.SpecAx_ref[0].set_data([], [])
                self.SpecAx_ref1[0].set_data([], [])
                self.specA_ref[0].set_data([], [])
                self.specB_ref[0].set_data([], [])
                self.acf_bvd_ref[0].set_data([], [])
                self.acf_bvd_ref1[0].set_data([], [])
                self.acf_bvd_ref2[0].set_data([], [])
                self.acf_bv_refa[0].set_data([], [])
                self.acf_bv_refb[0].set_data([], [])
                
                # self.SpecAx.clear()
                # self.specAB.clear()
                # self.acf_bvd.clear()
                # self.acf_bv.clear()
            except Exception as e:
                print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
                pass

    def clearPlots(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.clearBVDPlot()
        self.clearAllanPlot()
        self.clearSpecPlot()

    def RButClicked(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.SquidFeedBut.pressed and self.SquidFeedStatus == 'NEG':
            self.SquidFeedStatus = 'POS'
            self.SquidFeedBut.setText('Positive')
            self.SquidFeedBut.setStyleSheet(red_style)
        else:
            self.SquidFeedStatus = 'NEG'
            self.SquidFeedBut.setText('Negative')
            self.SquidFeedBut.setStyleSheet(blue_style)

    def CurrentButClicked(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.CurrentBut.pressed and self.CurrentButStatus == 'I1':
            self.CurrentButStatus = 'I2'
            self.CurrentBut.setText('I2')
            self.CurrentBut.setStyleSheet(blue_style)
        else:
            self.CurrentButStatus = 'I1'
            self.CurrentBut.setText('I1')
            self.CurrentBut.setStyleSheet(red_style)

    def getData(self) -> None:
        """
        This function performs the following when called:
            1. Reads all magnicon ccc text files
            2. Calculates the bridge voltage difference (BVD) using the raw text files and checks
               the bvd calculations against the _bvd.text files
            3. Uses the BVD to compute resistance ratio and values
            4. Sets the results in the GUI
            5. Plots the results in the GUI
        """
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        getData_start = perf_counter()
        if self.txtFilePath.endswith('_bvd.txt') and os.path.exists(self.txtFilePath) and self.txtFilePath.split('_bvd.txt')[0][-1].isnumeric():
            self.txtFile = self.txtFilePath.split('/')[-1]
            self.pathString = self.txtFilePath.split('_bvd.txt')[0]
            self.dat = magnicon_ccc(self.txtFilePath)
            getFile_end = perf_counter() - getData_start
            print("Time taken to read files: " +  str(getFile_end))
            if len(self.dat.bvd) > 0:
                self.validFile = True
            else:
                self.validFile = False
            # print("File Validity: ", self.validFile)
            # get the standard temperature for the two resistors if they exist
            try:
                self.R1Temp = self.dat.R1stdTemp
                self.R2Temp = self.dat.R2stdTemp
            except:
                self.R1Temp = 25
                self.R2Temp = 25
                pass
            self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))

            self.cleanUp()
            # getResults_end = perf_counter() - getData_start
            # print("Time taken to get Results: " + str(getResults_end))
            if self.validFile:
                self.getBVD()
                getBVD_end = perf_counter() - getData_start
                print("Time taken to get BVD: " +  str(getBVD_end))
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
                self.plotStatMeasures()
                getPlot_end = perf_counter() - getData_start
                print("Time taken to plot all data in GUI: ", str(getPlot_end))
                getData_end = perf_counter() - getData_start
                print("Time taken to get and analyze data: " +  str(getData_end))
                self.statusbar.showMessage('Time taken to process and display data ' + str("{:2.2f}".format(getData_end)) + ' s', 5000)
            else:
                self.setInvalidData()
                self.statusbar.showMessage('Invalid file selected...', 5000)
                # self.clearPlots()
        else:
            # self.clearPlots()
            self.setInvalidData()
            self.statusbar.showMessage('Invalid file! Filename should end in _bvd.txt', 5000)
        
        
       
        

    def plotStatMeasures(self,) -> None:
        self.plotSpec()
        self.plotAdev()

    def plotAdev(self,) -> None:
        self.overlapping = self.is_overlapping(self.OverlappingComboBox.currentText())
        self.plotAllan()

    def getBVD(self,):
        """Calculates the BVD from the raw text file only.
        Returns
        -------
        None.
        """
        try:
            # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
            self.bvd_stat_obj = bvd_stat(self.txtFilePath, int(self.SampUsedLineEdit.text()), self.dat)
            self.bvdList, self.V1, self.V2, self.A, self.B, self.stdA, self.stdB = self.bvd_stat_obj.send_bvd_stats()
            for i in range(len(self.bvdList)):
                self.bvdCount.append(i)
            self.bvd_stat_obj.clear_bvd_stats()
        except Exception as e:
            self.bvdList, self.V1, self.V2, self.A, self.B, self.stdA, self.stdB = [], [], [], [], [], [], []
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            pass
        # print(len(self.A), len(self.B))

    # Results from data
    def results(self, mag, T1: float, T2: float, P1: float, P2: float) -> None:
        if mag.deltaNApN1 == '':
            self.k = 0
            # (mag.N1*2048*mag.rangeShunt)
        else:
            self.k     = mag.deltaNApN1/mag.NA
        # correction factor for R1 and R2 due to temperature and pressure
        R1corr     = (mag.R1alpha*(T1-mag.R1stdTemp) + mag.R1beta*(T1-mag.R1stdTemp)**2) + (mag.R1pcr*(P1-101325))/1000
        R2corr     = (mag.R2alpha*(T2-mag.R2stdTemp) + mag.R2beta*(T2-mag.R2stdTemp)**2) + (mag.R2pcr*(P2-101325))/1000
        
        self.R2STPPred = mag.R2Pred
        if not self.changedR1STPBool:
            self.R1PPM = R1corr + mag.R1Pred
            self.R1STPPred = mag.R1Pred
        else:
            self.R1PPM = R1corr + float(self.R1STP)
            self.R1STPPred = float(self.R1STP)
        if not self.changedR2STPBool:
            self.R2PPM = R2corr + mag.R2Pred
            self.R2STPPred = mag.R2Pred
        else:
            self.R2PPM = R2corr + float(self.R2STP)
            self.R2STPPred = float(self.R2STP)
        self.R1    = (self.R1PPM/1000000 + 1) * mag.R1NomVal
        self.R2    = (self.R2PPM/1000000 + 1) * mag.R2NomVal
        # print (self.R1, self.R2)
        self.ratioMeanList = []
        self.R1List   = []
        self.R2List   = []
        ratioMeanC1   = []
        ratioMeanC2   = []
        self.C1R1List = []
        self.C1R2List = []
        self.C2R1List = []
        self.C2R2List = []
        if self.changedDeltaI2R2Ct != 0:
            myDeltaI2R2 = float(self.le_deltaI2R2.text())
        else:
            myDeltaI2R2 = float(mag.deltaI2R2)
        for i, V1 in enumerate(self.V1):
            # This calculation is done using the bridge voltages i.e the raw text file
            if mag.N2 != 0 and mag.N1 != 0 and myDeltaI2R2 != 0 and mag.R2NomVal != 0 and mag.R1NomVal != 0:
                self.ratioMeanList.append(mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.bvdList[i]/myDeltaI2R2))
                self.R1List.append((self.R1/self.ratioMeanList[i] - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
                self.R2List.append((self.R2*self.ratioMeanList[i] - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
                ratioMeanC1.append(mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.V1[i]/myDeltaI2R2))
                ratioMeanC2.append(mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.V2[i]/myDeltaI2R2))
                self.C1R1List.append((self.R1/ratioMeanC1[i] - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
                self.C1R2List.append((self.R2*ratioMeanC1[i] - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
                self.C2R1List.append((self.R1/ratioMeanC2[i] - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
                self.C2R2List.append((self.R2*ratioMeanC2[i] - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
            else:
                self.R1List.append(0)
                self.R2List.append(0)
        if  self.ratioMeanList != []:
            self.meanR1     = mean(self.R1List)
            self.meanR2     = mean(self.R2List)
            self.stdppm     = std(self.ratioMeanList, ddof=1)/mean(self.ratioMeanList)
            self.stdR1ppm   = std(self.R1List, ddof=1)
            self.stdR2ppm   = std(self.R2List, ddof=1)
            self.stdMeanPPM = self.stdppm/sqrt(len(self.R1List))
            self.C1R1       = mean(self.C1R1List)
            self.C1R2       = mean(self.C1R2List)
            self.C2R1       = mean(self.C2R1List)
            self.C2R2       = mean(self.C2R2List)
            self.stdC1R1    = std(self.C1R1List, ddof=1)
            self.stdC1R2    = std(self.C1R2List, ddof=1)
            self.stdC2R1    = std(self.C2R1List, ddof=1)
            self.stdC2R2    = std(self.C2R2List, ddof=1)
            self.stdMeanR1 = self.stdR1ppm/sqrt(len(self.R1List))
            self.stdMeanR2 = self.stdR2ppm/sqrt(len(self.R2List))
        else:
            self.meanR1     = nan
            self.meanR2     = nan
            self.stdppm     = nan
            self.stdR1ppm   = nan
            self.stdR2ppm   = nan
            self.stdMeanPPM = nan
            self.C1R1       = nan
            self.C1R2       = nan
            self.C2R1       = nan
            self.C2R2       = nan
            self.stdC1R1    = nan
            self.stdC1R2    = nan
            self.stdC2R1    = nan
            self.stdC2R2    = nan
            self.stdMeanR1  = nan
            self.stdMeanR2  = nan

        if self.bvdList != []:
            self.N         = len(self.bvdList)
            self.bvd_mean   = mean(self.bvdList)
            self.std       = std(self.bvdList, ddof=1)
            self.stdMean   = self.std/sqrt(len(self.bvdList))
        else:
            self.bvd_mean = nan
            self.std = nan
            self.stdMean = nan

        if mag.bvd != []:
            self.bvdList_chk = mag.bvd
            self.bvd_mean_chk = mean(self.bvdList_chk)
            self.bvd_std_chk = std(mag.bvd, ddof=1)
            self.bvd_stdmean_chk = self.bvd_std_chk/sqrt(len(self.bvdList_chk))
        else:
            self.bvd_mean_ck = nan
            self.bvd_std_chk = nan
            self.bvd_stdmean_chk = nan
            
        if mag.N2 != 0 and mag.N1 != 0 and myDeltaI2R2 != 0 and mag.R2NomVal != 0 and mag.R1NomVal != 0:
            self.ratioMean = mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.bvd_mean/myDeltaI2R2) # calculated from raw bridge voltages
            self.ratioMeanChk   = mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))*(1 + self.bvd_mean_chk/myDeltaI2R2) # calculated from bvd file
            self.R1MeanChk = (self.R1/self.ratioMeanChk - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr
            self.R2MeanChk = (self.R2*self.ratioMeanChk - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr

            self.R1CorVal = ((self.R1STPPred/1000000 + 1) * mag.R1NomVal)
            self.R2CorVal = ((self.R2STPPred/1000000 + 1) * mag.R2NomVal)

            self.R1MeanChkOhm = (self.meanR2/1000000 + 1) * mag.R1NomVal
            self.R2MeanChkOhm = (self.meanR1/1000000 + 1) * mag.R2NomVal
        else:
            self.ratioMean = nan
            self.ratioMeanChk = nan
            self.R1MeanChk = nan
            self.R2MeanChk = nan
            self.R1CorVal = nan
            self.R2CorVal = nan
            self.R1MeanChkOhm = nan
            self.R2MeanChkOhm = nan
            # self.remTime      = mag.measTime - (self.N*mag.fullCyc)
            # self.remTimeStamp = mag.sec2ts(self.remTime)

    def setValidData(self) -> None:
        """Sets the texts in all GUI line edits and spin boxes

        Returns
        -------
        None
        """
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.VMeanLineEdit.setText(str("{:.6e}".format(self.bvd_mean)))
        self.VMeanChkLineEdit.setText(str("{:.6e}".format(self.bvd_mean_chk)))
        self.Current1LineEdit.setText(str(self.dat.I1))
        self.FullCycLineEdit.setText(str(self.dat.fullCyc))
        if self.SampUsedCt != 0:
            delay = ((self.dat.SHC - int(self.SampUsedLineEdit.text()))/self.dat.SHC)*(self.dat.SHC*self.dat.intTime/self.dat.timeBase - self.dat.rampTime)
            meas = (self.dat.SHC*self.dat.intTime/self.dat.timeBase) - self.dat.rampTime - delay
            self.DelayLineEdit.setText(str("{:2.2f}".format(delay)))
            self.MeasLineEdit.setText(str("{:2.2f}".format(meas)))
        else:
            self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))
            self.DelayLineEdit.setText(str("{:2.2f}".format(self.dat.delay)))
            self.MeasLineEdit.setText(str("{:2.2f}".format(self.dat.meas)))
        if self.changedDeltaI2R2Ct == 0:
            self.le_deltaI2R2.setText(str(self.dat.deltaI2R2))
        self.R1SNLineEdit.setText(self.dat.R1SN)
        self.Current2LineEdit.setText(str(self.dat.I2))
        self.N2LineEdit.setText(str(self.dat.N2))
        self.NAuxLineEdit.setText(str(self.dat.NA))
        self.AppVoltLineEdit.setText(str("{:.9}".format(self.dat.appVolt)))
        self.R2SNLineEdit.setText(self.dat.R2SN)
        self.SHCLineEdit.setText(str(self.dat.SHC))
        self.N1LineEdit.setText(str(self.dat.N1))
        self.CommentsTextBrowser.setText(self.dat.comments)
        self.RelHumLineEdit.setText(str(self.dat.relHum))
        self.kLineEdit.setText(str("{:2.9f}".format(self.k)))
        if self.k == 0:
            self.kLineEdit.setStyleSheet("color: red")
        else:
            self.kLineEdit.setStyleSheet("color: black")
        self.R1TempLineEdit.setText(str("{:.5f}".format(self.R1Temp)))
        self.R2TempLineEdit.setText(str("{:.5f}".format(self.R2Temp)))
        self.R1PresLineEdit.setText(str(self.R1pres))
        self.R2PresLineEdit.setText(str(self.R2pres))
        self.R1OilPresLineEdit.setText(str(self.R1OilPres))
        self.R2OilPresLineEdit.setText(str(self.R2OilPres))
        self.R1TotalPresLineEdit.setText(str("{:.2f}".format(self.R1TotPres)))
        self.R2TotalPresLineEdit.setText(str("{:.2f}".format(self.R2TotPres)))
        # self.updateOilDepth('both')
        self.R1STPLineEdit.setText(str("{:2.7f}".format(self.R1STPPred)))
        self.R2STPLineEdit.setText(str("{:2.7f}".format(self.R2STPPred)))
        self.RampLineEdit.setText(str(self.dat.rampTime))
        self.MeasCycLineEdit.setText(str(int(self.dat.measCyc)))
        self.RatioMeanLineEdit.setText(str("{:.12f}".format(self.ratioMean)))
        self.StdDevLineEdit.setText(str("{:.6e}".format(self.std)))
        self.StdDevChkLineEdit.setText(str("{:.6e}".format(self.bvd_std_chk)))
        self.StdDevMeanLineEdit.setText(str("{:.6e}".format(self.stdMean)))
        self.StdDevMeanChkLineEdit.setText(str("{:.6e}".format(self.bvd_stdmean_chk)))
        self.StdDevChkPPMLineEdit.setText(str("{:.7f}".format(self.stdppm*10**6)))
        self.NLineEdit.setText(str(self.N))
        self.MeasTimeLineEdit.setText(self.dat.measTimeStamp)
        self.MDSSButton.setStyleSheet(red_style)
        self.MDSSButton.setEnabled(True)
        self.plotCountCombo.clear()
        self.SetResTab.update()

        for i in range(len(self.bvdList)):
            self.plotCountCombo.addItem(f'Count {i}')

        if len(self.bvdList) > 400:
            self.bins = int(sqrt(len(self.bvdList)))
        else:
            self.bins = 20
        self.stdR(self.RButStatus)

    def setInvalidData(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.validFile = False
        self.VMeanLineEdit.setText("")
        self.VMeanChkLineEdit.setText("")
        self.Current1LineEdit.setText("")
        self.FullCycLineEdit.setText("")
        self.MeasCycLineEdit.setText("")
        self.SampUsedLineEdit.setText("")
        self.RampLineEdit.setText("")
        self.DelayLineEdit.setText("")
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
        self.le_deltaI2R2.setText("")
        self.kLineEdit.setText("")
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

    def stdR(self, R: str) -> None:
        """ Depending on the standard resistor [R1 or R2], the value of the unknown
            is set in the line edit
        Parameters
        ----------
        R : str, Resistor position [R1 or R2]

        Returns
        -------
        None
            DESCRIPTION.
        """
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if R == 'R1':
            self.R1ValueLineEdit.setText(str("{:5.10f}".format(self.R1)))
            self.R2ValueLineEdit.setText(str("{:5.10f}".format(self.dat.R2NomVal)))
            self.R2PPMLineEdit.setText(str(0))
            self.ppmMeanLineEdit.setText(str("{:.7f}".format(self.meanR1)))
            self.RMeanChkPPMLineEdit.setText(str("{:.7f}".format(self.R1MeanChk)))
            self.C1LineEdit.setText(str("{:.7f}".format(self.C1R1)))
            self.C2LineEdit.setText(str("{:.7f}".format(self.C2R1)))
            self.C1C2LineEdit.setText(str("{:.7f}".format(self.C1R1-self.C2R1)))
            self.StdDevC1LineEdit.setText(str("{:.7f}".format(self.stdC1R1)))
            self.StdDevC2LineEdit.setText(str("{:.7f}".format(self.stdC2R1)))
            self.StdDevPPMLineEdit.setText(str("{:.7f}".format(self.stdR1ppm)))
            self.StdDevMeanPPMLineEdit.setText(str("{:.7f}".format(self.stdMeanR1)))
            if self.R1PPM:
                self.R1PPMLineEdit.setText(str("{:2.7f}".format(self.R1PPM)))
            else:
                self.R1PPMLineEdit.setText(str(0))
        else:
            self.R1ValueLineEdit.setText(str("{:5.10f}".format(self.dat.R1NomVal)))
            self.R2ValueLineEdit.setText(str("{:5.10f}".format(self.R2)))
            self.R1PPMLineEdit.setText(str(0))
            self.ppmMeanLineEdit.setText(str("{:.7f}".format(self.meanR2)))
            self.RMeanChkPPMLineEdit.setText(str("{:.7f}".format(self.R2MeanChk)))
            self.C1LineEdit.setText(str("{:.7f}".format(self.C1R2)))
            self.C2LineEdit.setText(str("{:.7f}".format(self.C2R2)))
            self.C1C2LineEdit.setText(str("{:.7f}".format(self.C1R2-self.C2R2)))
            self.StdDevC1LineEdit.setText(str("{:.7f}".format(self.stdC1R2)))
            self.StdDevC2LineEdit.setText(str("{:.7f}".format(self.stdC2R2)))
            self.StdDevPPMLineEdit.setText(str("{:.7f}".format(self.stdR2ppm)))
            self.StdDevMeanPPMLineEdit.setText(str("{:.7f}".format(self.stdMeanR2)))
            if self.R2PPM:
                self.R2PPMLineEdit.setText(str("{:2.7f}".format(self.R2PPM)))
            else:
                self.R2PPMLineEdit.setText(str(0))

    def R1PresChanged(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        try:
            self.R1pres    = float(self.R1PresLineEdit.text())
            self.R1TotPres = self.R1pres + self.R1OilPres
            self.R1TotalPresLineEdit.setText(str("{:.4f}".format(self.R1TotPres)))
            if self.bvd_stat_obj is not None:
                self.cleanUp()
                self.getBVD()
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            self.R1PresLineEdit.setText(str("{:.4f}".format(self.R1Totpres)))
            pass

    def R2PresChanged(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        try:
            self.R2pres    = float(self.R2PresLineEdit.text())
            self.R2TotPres = self.R2pres + self.R2OilPres
            self.R2TotalPresLineEdit.setText(str("{:.4f}".format(self.R2TotPres)))
            if self.bvd_stat_obj is not None:
                self.cleanUp()
                self.getBVD()
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            self.R2PresLineEdit.setText(str("{:.4f}".format(self.R2Totpres)))
            pass

    def oilDepth1Changed(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.R1OilDepth = self.R1OilDepthSpinBox.value()
        self.updateOilDepth('R1')
        if self.bvd_stat_obj is not None:
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)

    def oilDepth2Changed(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.R2OilDepth = self.R2OilDepthSpinBox.value()
        self.updateOilDepth('R2')
        if self.bvd_stat_obj is not None:
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)

    def updateOilDepth(self, R: str) -> None:
        global g
        global c
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if R == 'R1' or R == 'both':
            self.R1OilPres = c*g*self.R1OilDepth
            self.R1OilPresLineEdit.setText(str("{:.4f}".format(self.R1OilPres)))
            self.R1TotPres = self.R1pres + self.R1OilPres
            self.R1TotalPresLineEdit.setText(str("{:.4f}".format(self.R1TotPres)))
            self.R1OilDepthSpinBox.setValue(self.R1OilDepth)
        if R == 'R2' or R == 'both':
            self.R2OilPres = c*g*self.R2OilDepth
            self.R2OilPresLineEdit.setText(str("{:.4f}".format(self.R2OilPres)))
            self.R2TotPres = self.R2pres + self.R2OilPres
            self.R2TotalPresLineEdit.setText(str("{:.4f}".format(self.R2TotPres)))
            self.R2OilDepthSpinBox.setValue(self.R2OilDepth)

    def temp1Changed(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        try:
            self.R1Temp = float(self.R1TempLineEdit.text())
            if self.bvd_stat_obj is not None:
                self.cleanUp()
                self.getBVD()
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            self.R1TempLineEdit.setText(str("{:.4f}".format(self.R1Temp)))
            pass

    def temp2Changed(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        try:
            self.R2Temp = float(self.R2TempLineEdit.text())
            if self.bvd_stat_obj is not None:
                self.cleanUp()
                self.getBVD()
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
        except Exception as e:
            print("In function: " +  inspect.stack()[0][3] + " Exception: " + str(e))
            self.R2TempLineEdit.setText(str("{:.4f}".format(self.R2Temp)))
            pass

    def folderClicked(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.dialog.exec():
            self.txtFilePath = self.dialog.selectedFiles()[0]
            print('Loading datafile: ', self.txtFilePath)
        self.txtFileLineEdit.setText(self.txtFilePath)
        self.validFile = False
        self.getData()

    def folderEdited(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.txtFilePath = self.txtFileLineEdit.text()
        self.validFile = False
        self.getData()

    def MDSSClicked(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
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
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.mdssdir = "C:" + os.sep + "Users" + os.sep + os.getlogin() + os.sep + "Desktop" + os.sep + r"Transfer Files"
        if not os.path.isdir(self.mdssdir):
            os.mkdir(self.mdssdir)
        self.statusbar.showMessage('Saving...', 2000)
        self.progressBar.setProperty('value', 25)
        self.saveStatus = False
        self.MDSSButton.setStyleSheet(red_style)
        self.MDSSButton.setText('No')
        self.saveButton.setEnabled(False)
        self.dat.comments = self.CommentsTextBrowser.toPlainText()
        writeDataFile(savepath=self.mdssdir, text=self.txtFile, dat_obj=self.dat, \
                      bvd_stat_obj=self.bvd_stat_obj, RStatus=self.RButStatus, \
                      R1Temp=self.R1Temp, R2Temp=self.R2Temp, R1Pres=self.R1TotPres, \
                      R2Pres=self.R2TotPres, I=self.CurrentButStatus, \
                      polarity=self.SquidFeedStatus, system=self.MagElecComboBox.currentText(), \
                      probe=self.ProbeComboBox.currentText(), meanR1=self.meanR1, meanR2=self.meanR2, \
                      stdR1ppm=self.stdR1ppm, stdR2ppm=self.stdR2ppm, R1MeanChkOhm=self.R1MeanChkOhm, \
                      R2MeanChkOhm=self.R2MeanChkOhm, C1R1=self.C1R1, C2R1=self.C2R1, \
                      stdC1R1=self.stdC1R1, stdC2R1=self.stdC2R1, C1R2=self.C1R2, \
                      C2R2=self.C2R2, stdC1R2=self.stdC1R2, stdC2R2=self.stdC2R2,\
                      R1PPM=self.R1PPM, R2PPM=self.R2PPM, bvd_mean=self.bvd_mean, \
                      N=self.N, samplesUsed=int(self.SampUsedLineEdit.text()), \
                      meas=float(self.MeasLineEdit.text()), delay=float(self.DelayLineEdit.text()))
        
        with open(self.pathString + '_pyCCCRAW.mea', 'w') as mea_file:
            if self.RButStatus == 'R1':
                unk = 'R2'
            else:
                unk = 'R1'
            mea_file.write('# Standard: ' +  str(self.RButStatus) + '\n' + '# Unknown: ' + str(unk) + '\n' + \
                           '# Start Time: ' + str(self.dat.startDate) + '\n' + '# End Time: ' + str(self.dat.endDate) + '\n' + \
                           '# R1 Serial: ' + str(self.dat.R1SN) + '\n' + '# R1 PPM: ' + str(self.R1PPM) + '\n' + \
                           '# R1 Value: ' + str(self.R1) + '\n' + '# R2 Serial: ' + str(self.dat.R2SN) + '\n' + \
                           '# R2 PPM: ' + str(self.R2PPM) + '\n' + '# R2 Value: ' + str(self.R2) + '\n' + \
                           '# R1 Current: ' + str(self.dat.I1) + '\n' + '# R2 Current: ' + str(self.dat.I2) + '\n' + \
                           '# N1: ' + str(self.dat.N1) + '\n' + '# N2: ' + str(self.dat.N2) + '\n' + \
                           '# Meas/Stats: ' + str(self.SHCLineEdit.text() + '/' + self.SampUsedLineEdit.text()) + '\n' + '# Full Cycle Time: ' + str(self.FullCycLineEdit.text()) + '\n' + \
                           '# Ramp Time: ' + str(self.RampLineEdit.text()) + '\n' + '# Measurement Time: ' + str(self.MeasLineEdit.text()) + '\n' + \
                           '# Delay: ' + str(self.DelayLineEdit.text()) + '\n\n') 

        with open(self.pathString + '_CCCRAW.mea', 'a') as mea_file:
            for i, j, in zip(self.bvdList, self.ratioMeanList):
                mea_file.write(str(i) + '\t' + str(j) + '\n')
        self.progressBar.setProperty('value', 100)
        self.statusbar.showMessage('Done', 2000)

    def cleanUp(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.deletedV1      = []
        self.deletedV2      = []
        self.deletedCount   = []
        self.deletedBVD     = []
        self.deletedBVDChk  = []

        self.bvdList        = []
        self.bvdCount       = []
        self.deletedR1      = []
        self.deletedR2      = []

        self.SampUsedCt     = 0
        self.changedDeltaI2R2Ct = 0
        self.changedR1STPBool = False
        self.changedR2STPBool = False

    def deleteBut(self) -> None:
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.plottedBVD and self.plotCountCombo.count():
            curIndex = self.plotCountCombo.currentIndex()
            self.deletedIndex.append(curIndex)
            self.deletedCount.append(int(self.plotCountCombo.currentText().replace('Count ', '')))
            self.deletedBVD.append(self.bvdList[curIndex])
            self.deletedBVDChk.append(self.bvdList_chk[curIndex])
            self.deletedV1.append(self.V1[curIndex])
            self.deletedV2.append(self.V2[curIndex])
            self.deletedR1.append(self.R1List[curIndex])
            self.deletedR2.append(self.R2List[curIndex])
            self.plotCountCombo.removeItem(curIndex)
            self.V1.pop(curIndex)
            self.V2.pop(curIndex)
            self.bvdList.pop(curIndex)
            self.bvdList_chk.pop(curIndex)
            self.bvdCount.pop(curIndex)
            self.R1List.pop(curIndex)
            self.R2List.pop(curIndex)
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()
            self.plotAllan()

    def restoreDeleted(self) -> None:
        """Restore last deleted data point
        Parameters
        ----------
        loop : TYPE, optional
            DESCRIPTION. The default is None.
        Returns
        -------
        None
        """
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        if self.deletedCount != []:
            self.plotCountCombo.insertItem(self.deletedIndex[-1], f'Count {self.deletedCount[-1]}')
            self.V1.insert(self.deletedIndex[-1], self.deletedV1[-1])
            self.V2.insert(self.deletedIndex[-1], self.deletedV2[-1])
            self.bvdCount.insert(self.deletedIndex[-1], self.deletedCount[-1])
            self.bvdList.insert(self.deletedIndex[-1], self.deletedBVD[-1])
            self.bvdList_chk.insert(self.deletedIndex[-1], self.deletedBVDChk[-1])
            self.R1List.insert(self.deletedIndex[-1], self.deletedR1[-1])
            self.R2List.insert(self.deletedIndex[-1], self.deletedR2[-1])
            self.deletedIndex.pop(-1)
            self.deletedCount.pop(-1)
            self.deletedBVD.pop(-1)
            self.deletedBVDChk.pop(-1)
            self.deletedR1.pop(-1)
            self.deletedR2.pop(-1)
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()
            self.plotStatMeasures()

    def replotAll(self) -> None:
        """Replot all the data
        Returns
        -------
        None
        """
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.cleanUp()
        self.getBVD()
        self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        self.setValidData()
        self.plotBVD()
        self.plotStatMeasures()

if __name__ == "__main__":
    # print('In function: ' + inspect.stack()[0][3])
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec())