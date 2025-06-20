import sys, os
from time import perf_counter
import inspect

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt, QRect, QMetaObject, QCoreApplication
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainterPath, QPainter,\
                        QKeySequence, QDoubleValidator
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, \
                             QLabel, QPushButton, QComboBox, QTextBrowser, QTabWidget, \
                             QSpacerItem, QGridLayout, QLineEdit, QFrame, QSizePolicy, \
                             QMenuBar, QSpinBox, QToolButton, QStatusBar, \
                             QTextEdit, QFileDialog, QCheckBox, QMessageBox)

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import MaxNLocator, ScalarFormatter, MultipleLocator
import matplotlib.style as mplstyle
from numpy import sqrt, std, mean, ones, linspace, array, nan
from scipy import signal
import allantools

# custom imports
from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
from create_mag_ccc_datafile import writeDataFile
import mystat
from env import env
from argparse import ArgumentParser

import logging
from logging.handlers import TimedRotatingFileHandler

from threading import Thread

# base directory of the project
base_dir = os.path.dirname(os.path.abspath(__file__))
# Create the logger
logger = logging.getLogger(__name__)
# set the log level
logger.setLevel(logging.DEBUG)

# python globals
__version__ = '2.4' # Program version string
red_style   = "color: white; background-color: red"
blue_style  = "color: white; background-color: blue"
green_style = "color: white; background-color: green"
winSizeH    = 1000
winSizeV    = 845
#c           = 0.8465 # specific gravity of oil used
g           = 9.81 # local acceleration due to gravity
# I- == blue, I+ == Red
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
           'grid.alpha': 0.1,
           'grid.linewidth': 0.7,
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
    import pyi_splash
    # base_dir = os.path.dirname(sys.executable)
    running_mode = 'Frozen/executable'
else:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        running_mode = "Non-interactive (e.g. 'python Magnicon-Offline-Analyzer.py')"
    except NameError:
        base_dir = os.getcwd()
        running_mode = 'Interactive'

os.chdir(base_dir)
current_path = os.environ["PATH"]
new_path = current_path + os.pathsep + base_dir + r'\texlive\2024\bin\windows' + \
           os.pathsep + base_dir + r'\data' + os.pathsep + base_dir + r'\tex\latex\circuitikz' + \
           os.pathsep + base_dir + r'\texlive\texmf-local'
os.environ['PATH'] = new_path
os.environ['TEXMFHOME'] = base_dir + r'\texlive\texmf-local'
os.environ['TEXMFLOCAL'] = base_dir + r'\texlive\texmf-local'

from lcapy import Circuit
# import lcapy.scripts.schtex as schtex

class aboutWindow(QWidget):
    def __init__(self):
        """QWidget class for showing the About window to display general program
           information
        """
        global __version__
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon(base_dir + r'\icons\main.png'))
        self.setFixedSize(300, 200)
        self.te_about = QTextEdit()
        self.te_about.setReadOnly(True)
        self.te_about.setPlainText("Data Analysis software for the powerful Magnicon")
        self.te_about.append("CCC probe and electronics")
        self.te_about.append("Version " + str(__version__))
        self.te_about.append("Developers: Andrew Geckle & Alireza Panna")
        self.te_about.append("Maintainers: Alireza Panna")
        self.te_about.append("For reporting bugs or feature request contact Alireza Panna @")
        self.te_about.append("alireza.panna@nist.gov")
        layout = QVBoxLayout()
        layout.addWidget(self.te_about)
        self.setLayout(layout)

class timingDiagramWindow(QWidget):
    def __init__(self):
        """QWidget class for showing the timing diagram window to display CCC's
           sampling routing
        """
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        super(QWidget, self).__init__()
        self.setFixedSize(1105, 555)
        self.setWindowTitle("Timing Diagram: " + base_dir)
        self.setWindowIcon(QIcon(base_dir + r'\icons\main.png'))
        lbl_timing_diagram = QLabel(self)
        lbl_timing_diagram.setPixmap(QPixmap(base_dir + r'\icons\timing_diagram.PNG'))
        lbl_timing_diagram.show()
        layout = QVBoxLayout()
        layout.addWidget(lbl_timing_diagram)
        self.setLayout(layout)

class Ui_mainWindow(object):
    def setupUi(self, mainWindow) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        global winSizeH, winSizeV
        mainWindow.setFixedSize(winSizeH, winSizeV)
        mainWindow.setWindowIcon(QIcon(base_dir + r'\icons\main.png'))
        self.initializations()

        self.centralwidget = QWidget(parent=mainWindow)
        self.tabWidget = QTabWidget(parent=self.centralwidget)
        self.tabWidget.setGeometry(QRect(0, 0, winSizeH - 125, winSizeV))
        self.SetResTab = QWidget()
        self.SetResTab.paintEvent = lambda event: self._paintPath(event)
        self.CCCDiagramTabSetUp()
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
        self.voltageTabSetUp()
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

        self.timing_action = QAction("&Timing Diagram")
        self.timing_action.setStatusTip("Show timing diagram for CCC Measurements")
        self.timing_action.triggered.connect(self._showTimingDiagram)

        self.tooltip_action = QAction("&Show tooltip")
        self.tooltip_action.setStatusTip("Show/hide tooltip")
        self.tooltip_action.setCheckable(True)
        self.tooltip_action.triggered.connect(self._showToolTip)

        self.about_action = QAction("&About")
        self.about_action.setStatusTip("Program information & license")
        self.about_action.triggered.connect(self._about)

        mainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(parent=mainWindow)
        self.menubar.setGeometry(QRect(0, 0, winSizeH, 22))
        self._create_menubar()
        mainWindow.setMenuBar(self.menubar)

        self.dialog = QFileDialog(parent=mainWindow, )
        # self.dialog.setViewMode(QFileDialog.Detail)
        if site == 'NIST':
            if os.path.exists(r"\\elwood.nist.gov\68internal\Calibrations\MDSS Data\resist"):
                self.dialog.setDirectory(r"\\elwood.nist.gov\68internal\Calibrations\MDSS Data\resist\MagniconData\CCCViewerData")
            else:
                self.dialog.setDirectory(r"C:")
        else:
            self.dialog.setDirectory(r"C:")
        self.dialog.setNameFilters(["Text files (*_bvd.txt)"])
        self.dialog.selectNameFilter("Text files (*_bvd.txt)")
        self.temperature1_dialog = QFileDialog(parent=mainWindow)
        self.temperature2_dialog = QFileDialog(parent=mainWindow)
        if site == 'NIST':
            if os.path.exists(r"D:\Environment"):
                self.temperature1_dialog.setDirectory(r"D:\Environment")
                self.temperature2_dialog.setDirectory(r"D:\Environment")
            else:
                self.temperature1_dialog.setDirectory(r"C:")
                self.temperature2_dialog.setDirectory(r"C:")
        else:
            self.temperature1_dialog.setDirectory(r"C:")
            self.temperature2_dialog.setDirectory(r"C:")

        self.statusbar = QStatusBar(parent=mainWindow)
        mainWindow.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready", 2000)

        self.retranslateUi(mainWindow)
        self.tabWidget.setCurrentIndex(1)
        # Connect the currentChanged signal to a function
        self.tabWidget.currentChanged.connect(self.onTabChanged)
        QMetaObject.connectSlotsByName(mainWindow)
        # self.drawTimingDiagram()
        if getattr(sys, 'frozen', False):
            pyi_splash.close()
    
    def onTabChanged(self, index: int):
        if index == 0 and self.dat != None and self.draw_flag == False:
            try:
                self.draw_thread = Thread(target = self.CCCDiagram, args=(round(self.dat.R1NomVal, 2), round(self.dat.R2NomVal, 2), \
                                self.dat.N1, self.dat.N2, format(self.dat.I1, ".1e"), \
                                format(self.dat.I2, ".1e"), format(self.dat.bvdMean, ".1e"), \
                                self.dat.NA, "10k*" + str(self.dat.dac12), "10k/" + str(self.dat.rangeShunt), format(self.dat.I1*self.k, ".1e"),), daemon=True)
                self.draw_thread.start()
                self.draw_thread.join()
                self.draw_flag = True
            except Exception as e:
                logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + ' Error: ' + str(e))
                self.draw_flag == False
                if self.draw_thread is not None:
                    self.draw_thread.join()
                pass

    def drawTimingDiagram(self,):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.path = QPainterPath()
        self.shift_col4x = self.col4x - 5
        self.path.moveTo(self.shift_col4x, 400)
        self.path.lineTo(self.shift_col4x + 50, 350)
        self.path.lineTo(self.shift_col4x + 350, 350)

    def _paintPath(self, event):
        # TODO: lines where ramps are need to be shorter...
        ramp_max = 100 # 100 pixels corresponds to 10s of ramp time which is max
        y_start = 400
        y_end = 350
        painter = QPainter(self.SetResTab)
        # painter.begin(self.SetResTab)
        painter.setPen(self.black_pen)
        scale_factor = 1.0
        painter.scale(scale_factor, scale_factor)
        if self.IgnoredFirstLineEdit.text() != '' and self.IgnoredLastLineEdit.text() != '':
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
                if ct >= (int(self.IgnoredFirstLineEdit.text())):
                    if ct < (int(self.dat.SHC) - int(self.IgnoredLastLineEdit.text())):
                        painter.setPen(self.green_pen)
                        painter.drawLine(int(i), 355, int(i), 400)
        painter.end()

    def _create_menubar(self, ) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        # print('Class: Ui_mainWindow, In function: ' + inspect.stack()[0][3])
        self.file_menu = self.menubar.addMenu("&File")
        self.file_menu.addAction(self.file_action)
        self.file_menu.addAction(self.close_action)
        # self.file_menu.setShortcutEnabled(True)
        self.help_menu = self.menubar.addMenu("&Help")
        self.help_menu.addAction(self.tooltip_action)
        self.help_menu.addAction(self.timing_action)
        self.help_menu.addAction(self.about_action)

    def _about(self,) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.about_window = aboutWindow()
        self.about_window.show()

    def _showTimingDiagram(self, ) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.timing_window = timingDiagramWindow()
        self.timing_window.show()

    def _showToolTip(self, ) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.tooltip_action.isChecked():
            self.show_tooltip()
            self.tooltip_action.setText("Hide Tooltip")
        else:
            self.hide_tooltip()
            self.tooltip_action.setText("Show Tooltip")

    def closeEvent(self, event):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.stats_thread is not None:
            self.stats_thread.join()
        if self.plot_bvd_thread is not None:
            self.plot_bvd_thread.join()
        if self.draw_thread is not None:
            self.draw_thread.join()
        file_handler.close()
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        mainWindow.close()
        QtCore.QCoreApplication.instance().quit
        app.quit()

    def initializations(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        global g
        self.txtFilePath  = ''
        # flags
        self.validFile    = False
        self.outliers     = False
        self.plottedBVD   = False
        self.plottedRaw   = False
        self.plottedAllan = False
        self.plottedSpec  = False
        self.changedDeltaI2R2Ct = 0
        self.changedR1STPBool = False
        self.changedR2STPBool = False
        self.stats_thread = None
        self.plot_bvd_thread = None
        self.draw_thread = None
        self.draw_flag = False
        self.user_warn_msg = ""
        self.deletePressed = False
        self.restorePressed = False
        self.outlierPressed = False

        self.R1Temp     = 23
        self.R2Temp     = 23
        self.R1pres     = 101325
        self.R2pres     = 101325
        self.R1OilDepth = 0
        self.R2OilDepth = 0
        self.alpha      = 0.5
        self.R1OilPres  = c*g*self.R1OilDepth
        self.R2OilPres  = c*g*self.R2OilDepth
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
        self.bvdList      = []
        self.corr_bvdList = []
        self.bvdList_chk  = []
        self.V1           = []
        self.V2           = []
        self.A            = []
        self.B            = []
        self.stdA         = []
        self.stdB         = []

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
        global red_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
        self.lbl_range_shunt = QLabel(parent=self.SetResTab)
        self.lbl_range_shunt.setGeometry(QRect(self.col0x, 520, self.lbl_width, self.lbl_height))
        self.CommentsLabel = QLabel(parent=self.SetResTab)
        self.CommentsLabel.setGeometry(QRect(self.col0x, 540, self.lbl_width, self.lbl_height))
        self.txtFileLabel = QLabel(parent=self.SetResTab)
        self.txtFileLabel.setGeometry(QRect(self.col0x, 600, self.lbl_width, self.lbl_height))
        self.MagElecLabel = QLabel(parent=self.SetResTab)
        self.MagElecLabel.setGeometry(QRect(self.col0x, 660, self.lbl_width, self.lbl_height))
        self.ProbeLabel = QLabel(parent=self.SetResTab)
        self.ProbeLabel.setGeometry(QRect(self.col0x, 720, self.lbl_width, self.lbl_height))
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
        self.lbl_path_temperature1 = QLabel(parent=self.SetResTab)
        self.lbl_path_temperature1.setGeometry(QRect(self.col1x, 660, self.lbl_width, self.lbl_height))
        self.lbl_path_temperature2 = QLabel(parent=self.SetResTab)
        self.lbl_path_temperature2.setGeometry(QRect(self.col1x, 720, self.lbl_width, self.lbl_height))
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
        self.lbl_12bitdac = QLabel(parent=self.SetResTab)
        self.lbl_12bitdac.setGeometry(QRect(self.col2x-100, 520, self.lbl_width+40, self.lbl_height))
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
        self.lbl_start_time = QLabel(parent=self.SetResTab)
        self.lbl_start_time.setGeometry(QRect(self.col3x, 590, self.lbl_width, self.lbl_height))
        self.lbl_end_time = QLabel(parent=self.SetResTab)
        self.lbl_end_time.setGeometry(QRect(self.col3x, 610, self.lbl_width, self.lbl_height))
        self.SquidFeedLabel = QLabel(parent=self.SetResTab)
        self.SquidFeedLabel.setGeometry(QRect(self.col3x, 660, self.lbl_width, self.lbl_height))
        self.CurrentButLabel = QLabel(parent=self.SetResTab)
        self.CurrentButLabel.setGeometry(QRect(self.col3x, 720, self.lbl_width, self.lbl_height))
        self.lbl_calmode = QLabel(parent=self.SetResTab)
        self.lbl_calmode.setGeometry(QRect(self.col3x, 510, self.lbl_width, self.lbl_height))
        self.lbl_calmode_rbv = QLabel(parent=self.SetResTab)
        self.lbl_calmode_rbv.setGeometry(QRect(self.col3x+60, 510, self.lbl_width-80, self.lbl_height))
        self.lbl_calmode_rbv.setStyleSheet(red_style)
        self.lbl_cnOutput = QLabel(parent=self.SetResTab)
        self.lbl_cnOutput.setGeometry(QRect(self.col3x, 540, self.lbl_width, self.lbl_height))
        self.lbl_cnOutput_rbv = QLabel(parent=self.SetResTab)
        self.lbl_cnOutput_rbv.setGeometry(QRect(self.col3x+60, 540, self.lbl_width-80, self.lbl_height))
        self.lbl_cnOutput_rbv.setStyleSheet(red_style)
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
        self.ppmMeanLabel.setGeometry(QRect(self.col7x, 210, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLabel = QLabel(parent=self.centralwidget)
        self.RMeanChkPPMLabel.setGeometry(QRect(self.col7x, 270, self.lbl_width, self.lbl_height))
        self.StdDevPPM2Label = QLabel(parent=self.centralwidget)
        self.StdDevPPM2Label.setGeometry(QRect(self.col7x, 330, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLabel = QLabel(parent=self.centralwidget)
        self.StdDevMeanPPMLabel.setGeometry(QRect(self.col7x, 390, self.lbl_width, self.lbl_height))
        self.C1C2Label = QLabel(parent=self.centralwidget)
        self.C1C2Label.setGeometry(QRect(self.col7x, 450, self.lbl_width, self.lbl_height))
        self.RatioMeanLabel = QLabel(parent=self.centralwidget)
        self.RatioMeanLabel.setGeometry(QRect(self.col7x, 510, self.lbl_width, self.lbl_height))
        self.lbl_ratioStdMean = QLabel(parent=self.centralwidget)
        self.lbl_ratioStdMean.setGeometry(QRect(self.col7x, 570, self.lbl_width, self.lbl_height))
        self.IgnoredFirstLabel = QLabel(parent=self.centralwidget)
        self.IgnoredFirstLabel.setGeometry(QRect(self.col7x, 630, self.lbl_width, self.lbl_height))
        self.IgnoredLastLabel = QLabel(parent=self.centralwidget)
        self.IgnoredLastLabel.setGeometry(QRect(self.col7x, 690, self.lbl_width, self.lbl_height))
        self.lbl_error = QLabel(parent=self.centralwidget)
        self.lbl_error.setGeometry(QRect(self.col7x, 750, self.lbl_width, self.lbl_height))
        self.ResultsLabel = QLabel(parent=self.SetResTab)
        self.ResultsLabel.setGeometry(QRect(650, 12, self.lbl_width, self.lbl_height))
        self.ResultsLabel.setStyleSheet(
                """QLabel {color: blue; font-weight: bold; font-size: 10pt }""")
        self.SettingsLabel = QLabel(parent=self.SetResTab)
        self.SettingsLabel.setGeometry(QRect(220, 12, self.lbl_width, self.lbl_height))
        self.SettingsLabel.setStyleSheet(
                """QLabel {color: red; font-weight: bold; font-size: 10pt }""")
        self.lbl_ccceq = QLabel(parent=self.SetResTab)
        self.lbl_ccceq.setGeometry(QRect(640, 440, self.lbl_width+25, self.lbl_height))
        self.lbl_ccceq.setStyleSheet(
                """QLabel {color: green; font-weight: bold; font-size: 14pt }""")
        # self.LogoLabel = QLabel(parent=self.SetResTab)
        # self.LogoPixmap = QPixmap(base_dir + r'\icons\nist_logo.png')
        # self.LogoLabel.setPixmap(self.LogoPixmap)
        # self.LogoLabel.setGeometry(QRect(550, 700, 300, 76))
        self.lbl_equation = QLabel(parent=self.SetResTab)
        self.pixmap_equation = QPixmap(base_dir + r'\icons\ccc_equation.PNG')
        self.lbl_equation.setPixmap(self.pixmap_equation)
        self.lbl_equation.setGeometry(QRect(550, 475, 314, 222))
        
        # Create and show the warning dialog
        self.msgBox = QMessageBox()
        self.msgBox.setIcon(QMessageBox.Icon.Critical)
        self.msgBox.setWindowTitle("Warning!")
        self.msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.msgBox.setStyleSheet("color: red;")

    def setLineEdits(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
        self.R1PresLineEdit.setValidator(QDoubleValidator())
        self.R1PresLineEdit.returnPressed.connect(self.R1PresChanged)
        self.R2PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PresLineEdit.setGeometry(QRect(self.col0x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2PresLineEdit.setValidator(QDoubleValidator())
        self.R2PresLineEdit.returnPressed.connect(self.R2PresChanged)
        self.txtFileLineEdit = QLineEdit(parent=self.SetResTab)
        self.txtFileLineEdit.setGeometry(QRect(self.col0x, self.coly*10 + 30, int(self.lbl_width*2.8), self.lbl_height))
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
        self.le_path_temperature1 = QLineEdit(parent=self.SetResTab)
        self.le_path_temperature1.setGeometry(QRect(self.col1x, self.coly*11 + 30, self.lbl_width+80, self.lbl_height))
        self.le_path_temperature1.setStyleSheet("""QLineEdit { background-color: rgb(255, 255, 255); color: black }""")

        self.le_path_temperature2 = QLineEdit(parent=self.SetResTab)
        self.le_path_temperature2.setGeometry(QRect(self.col1x, self.coly*12 + 30, self.lbl_width+80, self.lbl_height))
        self.le_path_temperature2.setStyleSheet("""QLineEdit { background-color: rgb(255, 255, 255); color: black }""")

        self.le_range_shunt = QLineEdit(parent=self.SetResTab)
        self.le_range_shunt.setGeometry(QRect(self.col1x-40, self.coly*8+40, self.lbl_width-60, self.lbl_height))
        self.le_range_shunt.setReadOnly(True)
        self.le_range_shunt.setStyleSheet(
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
        self.R1TempLineEdit.setValidator(QDoubleValidator())
        self.R1TempLineEdit.returnPressed.connect(self.temp1Changed)
        self.R2TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TempLineEdit.setGeometry(QRect(self.col3x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R2TempLineEdit.setValidator(QDoubleValidator())
        self.R2TempLineEdit.returnPressed.connect(self.temp2Changed)
        self.RelHumLineEdit = QLineEdit(parent=self.SetResTab)
        self.RelHumLineEdit.setGeometry(QRect(self.col3x, self.coly*8, self.lbl_width, self.lbl_height))
        self.RelHumLineEdit.setReadOnly(True)
        self.RelHumLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.le_start_time = QLineEdit(parent=self.SetResTab)
        self.le_start_time.setGeometry(QRect(self.col3x, self.coly*9 + 30, self.lbl_width, self.lbl_height))
        self.le_start_time.setReadOnly(True)
        self.le_start_time.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.le_end_time = QLineEdit(parent=self.SetResTab)
        self.le_end_time.setGeometry(QRect(self.col3x, self.coly*10 + 30, self.lbl_width, self.lbl_height))
        self.le_end_time.setReadOnly(True)
        self.le_end_time.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black }""")
        self.le_12bitdac = QLineEdit(parent=self.SetResTab)
        self.le_12bitdac.setGeometry(QRect(self.col3x - 100, self.coly*8 + 40, self.lbl_width-20, self.lbl_height))
        self.le_12bitdac.setReadOnly(True)
        self.le_12bitdac.setStyleSheet(
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
        self.ppmMeanLineEdit.setGeometry(QRect(self.col7x, self.coly*4, self.lbl_width, self.lbl_height))
        self.ppmMeanLineEdit.setReadOnly(True)
        self.ppmMeanLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        self.RMeanChkPPMLineEdit = QLineEdit(parent=self.centralwidget)
        self.RMeanChkPPMLineEdit.setGeometry(QRect(self.col7x, self.coly*5, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLineEdit.setReadOnly(True)
        self.RMeanChkPPMLineEdit.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        
        self.StdDevPPM2LineEdit = QLineEdit(parent=self.centralwidget)
        self.StdDevPPM2LineEdit.setGeometry(QRect(self.col7x, self.coly*6, self.lbl_width, self.lbl_height))
        self.StdDevPPM2LineEdit.setReadOnly(True)
        self.StdDevPPM2LineEdit.setStyleSheet(
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
        self.le_ratioStdMean = QLineEdit(parent=self.centralwidget)
        self.le_ratioStdMean.setGeometry(QRect(self.col7x, self.coly*10, self.lbl_width, self.lbl_height))
        self.le_ratioStdMean.setReadOnly(True)
        self.le_ratioStdMean.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black; font-weight: bold }""")
        # self.SampUsedLineEdit = QLineEdit(parent=self.centralwidget)
        # self.SampUsedLineEdit.setGeometry(QRect(self.col7x, self.coly*11, self.lbl_width, self.lbl_height))
        # self.SampUsedLineEdit.setReadOnly(False)
        # self.SampUsedLineEdit.returnPressed.connect(self.changedSamplesUsed)
        self.IgnoredFirstLineEdit = QLineEdit(parent=self.centralwidget)
        self.IgnoredFirstLineEdit.setGeometry(QRect(self.col7x, self.coly*11, self.lbl_width, self.lbl_height))
        self.IgnoredFirstLineEdit.setReadOnly(False)
        self.IgnoredFirstLineEdit.returnPressed.connect(self.changedIgnoredFirst)

        self.IgnoredLastLineEdit = QLineEdit(parent=self.centralwidget)
        self.IgnoredLastLineEdit.setGeometry(QRect(self.col7x, self.coly*12, self.lbl_width, self.lbl_height))
        self.IgnoredLastLineEdit.setReadOnly(False)
        self.IgnoredLastLineEdit.returnPressed.connect(self.changedIgnoredLast)
        
        self.le_error = QLineEdit(parent=self.centralwidget)
        self.le_error.setGeometry(QRect(self.col7x, int(self.coly*12.5), self.lbl_width, self.lbl_height))
        self.le_error.setReadOnly(True)
        self.le_error.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: red; font-weight: bold }""")

    def hide_tooltip(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.R1SNLineEdit.setToolTip('')
        self.R2SNLineEdit.setToolTip('')
        self.AppVoltLineEdit.setToolTip('')
        self.N1LineEdit.setToolTip('')
        self.MeasCycLineEdit.setToolTip('')
        self.FullCycLineEdit.setToolTip('')
        self.R1PresLineEdit.setToolTip('')
        self.R2PresLineEdit.setToolTip('')
        self.txtFileLineEdit.setToolTip('')
        self.R1PPMLineEdit.setToolTip('')
        self.R2PPMLineEdit.setToolTip('')
        self.Current1LineEdit.setToolTip('')
        self.N2LineEdit.setToolTip('')
        self.SHCLineEdit.setToolTip('')
        self.RampLineEdit.setToolTip('')
        self.le_path_temperature1.setToolTip('')
        self.le_path_temperature2.setToolTip('')
        self.R1ValueLineEdit.setToolTip('')
        self.R2ValueLineEdit.setToolTip('')
        self.Current2LineEdit.setToolTip('')
        self.NAuxLineEdit.setToolTip('')
        self.DelayLineEdit.setToolTip('')
        self.MeasLineEdit.setToolTip('')
        self.R1OilPresLineEdit.setToolTip('')
        self.R2OilPresLineEdit.setToolTip('')
        self.kLineEdit.setToolTip('')
        self.MeasTimeLineEdit.setToolTip('')
        self.le_deltaI2R2.setToolTip('')
        self.R1TotalPresLineEdit.setToolTip('')
        self.R2TotalPresLineEdit.setToolTip('')
        self.R1TempLineEdit.setToolTip('')
        self.R2TempLineEdit.setToolTip('')
        self.RelHumLineEdit.setToolTip('')
        self.le_range_shunt.setToolTip('')
        self.le_12bitdac.setToolTip('')
        self.lbl_calmode_rbv.setToolTip('')
        self.le_start_time.setToolTip('')
        self.le_end_time.setToolTip('')
        self.VMeanLineEdit.setToolTip('')
        self.StdDevLineEdit.setToolTip('')
        self.StdDevMeanLineEdit.setToolTip('')
        self.C1LineEdit.setToolTip('')
        self.C2LineEdit.setToolTip('')
        self.VMeanChkLineEdit.setToolTip('')
        self.StdDevChkLineEdit.setToolTip('')
        self.StdDevMeanChkLineEdit.setToolTip('')
        self.StdDevC1LineEdit.setToolTip('')
        self.StdDevC2LineEdit.setToolTip('')
        self.R1STPLineEdit.setToolTip('')
        self.R2STPLineEdit.setToolTip('')
        self.NLineEdit.setToolTip('')
        self.StdDevPPMLineEdit.setToolTip('')
        self.StdDevChkPPMLineEdit.setToolTip('')
        self.ppmMeanLineEdit.setToolTip('')
        self.RMeanChkPPMLineEdit.setToolTip('')
        self.StdDevPPM2LineEdit.setToolTip('')
        self.StdDevMeanPPMLineEdit.setToolTip('')
        self.RatioMeanLineEdit.setToolTip('')
        self.le_ratioStdMean.setToolTip('')
        self.IgnoredFirstLineEdit.setToolTip('')
        self.IgnoredLastLineEdit.setToolTip('')
        self.le_error.setToolTip('')
        self.MagElecComboBox.setToolTip('')
        self.ProbeComboBox.setToolTip('')
        self.R1OilDepthSpinBox.setToolTip('')
        self.R2OilDepthSpinBox.setToolTip('')
        self.folderToolButton.setToolTip('')
        self.btn_temperature1.setToolTip('')
        self.btn_temperature2.setToolTip('')
        self.SquidFeedBut.setToolTip('')
        self.CurrentBut.setToolTip('')
        self.StandardRBut.setToolTip('')
        self.MDSSButton.setToolTip('')
        self.saveButton.setToolTip('')
        self.C1C2LineEdit.setToolTip('')
        self.chb_outlier.setToolTip('')

    def show_tooltip(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.R1SNLineEdit.setToolTip('Serial number for primary (R<sub>1</sub>) resistor')
        self.R2SNLineEdit.setToolTip('Serial number for secondary (R<sub>2</sub>) resistor')
        self.AppVoltLineEdit.setToolTip('Applied Voltage in volts')
        self.N1LineEdit.setToolTip('Primary winding turns')
        self.MeasCycLineEdit.setToolTip('Total number of measurements')
        self.FullCycLineEdit.setToolTip('Period of one full cycle')
        self.R1PresLineEdit.setToolTip('Air pressure for the primary (R<sub>1</sub>) resistor')
        self.R2PresLineEdit.setToolTip('Air pressure for the secondary (R<sub>2</sub>) resistor')
        self.txtFileLineEdit.setToolTip('Path for the _bvd.txt file')
        self.R1PPMLineEdit.setToolTip(f'Value for R<sub>1</sub> in {chr(956)}{chr(937)}/{chr(937)} corrected for environmentals')
        self.R2PPMLineEdit.setToolTip(f'Value for R<sub>2</sub> in {chr(956)}{chr(937)}/{chr(937)} corrected for environmentals')
        self.Current1LineEdit.setToolTip('DC Current in the primary ratio arm. (This is a 16 bit DAC value setting from CCC Viewer)')
        self.N2LineEdit.setToolTip('Secondary winding turns')
        self.SHCLineEdit.setToolTip('Number of samples in a half cycle')
        self.RampLineEdit.setToolTip('Ramp time in seconds')
        self.le_path_temperature1.setToolTip('path to the environments file for the primary resistor')
        self.le_path_temperature2.setToolTip('Path to the environments file for the secondary resistor')
        self.R1ValueLineEdit.setToolTip('Value of the primary resistor corrected for environmentals')
        self.R2ValueLineEdit.setToolTip('Value of the secondary resistor corrected for environmentals')
        self.Current2LineEdit.setToolTip('DC Current in the secondary ratio arm. (This is a 16 bit DAC value setting from CCC Viewer)')
        self.NAuxLineEdit.setToolTip('Auxillary winding turns')
        self.DelayLineEdit.setToolTip('Settle time in a half cycle, measurements during this time are ignored')
        self.MeasLineEdit.setToolTip('Measurement time in a half cycle')
        self.R1OilPresLineEdit.setToolTip('Oil pressure for the primary resistor')
        self.R2OilPresLineEdit.setToolTip('Oil pressure for the secondary resistor')
        self.kLineEdit.setToolTip('coupling constant = I<sub>1</sub>/I<sub>A</sub>')
        self.MeasTimeLineEdit.setToolTip('Total time taken for the measurement to complete')
        self.le_deltaI2R2.setToolTip('Peak-to-Peak voltage in the secondary ratio arm. This is a calculated value and should be checked regularly')
        self.R1TotalPresLineEdit.setToolTip('Total pressure experienced by the primary resistor')
        self.R2TotalPresLineEdit.setToolTip('Total pressure experienced by the secondary resistor')
        self.R1TempLineEdit.setToolTip('Temperature of the primary resistor')
        self.R2TempLineEdit.setToolTip('Temperature of the secondary resistor')
        self.RelHumLineEdit.setToolTip('Relative Humidity of the CCC Drive Electronics Chassis')
        self.le_range_shunt.setToolTip('Range shunt setting of the compensation network')
        self.le_12bitdac.setToolTip('12 bit DAC setting of the compensation network/16 bit correction setting (this should be 0 in normal operation)')
        self.lbl_calmode_rbv.setToolTip('Calibrated Mode')
        self.le_start_time.setToolTip('Start date and time of the measurement')
        self.le_end_time.setToolTip('End date and time of the measurement')
        self.VMeanLineEdit.setToolTip('Mean of the bridge voltage difference (C<sub>1</sub> + C<sub>2</sub>)/2 calculated from the raw .txt file')
        self.StdDevLineEdit.setToolTip('Standard deviation of the bridge voltage difference calculated from the raw .txt file')
        self.StdDevMeanLineEdit.setToolTip('Standard deviation of the mean of the bridge voltage difference calculated from the raw .txt file')
        self.C1LineEdit.setToolTip('Bridge voltage difference measured after t<sub>ramp</sub> + t<sub>settle</sub>  + t<sub>meas</sub>/2')
        self.C2LineEdit.setToolTip('Bridge voltage difference measured after t<sub>ramp</sub> + t<sub>settle</sub>')
        self.VMeanChkLineEdit.setToolTip('Mean of the bridge voltage difference calculated from the _bvd.txt file')
        self.StdDevChkLineEdit.setToolTip('Standard deviation of the bridge voltage difference calculated from the _bvd.txt file')
        self.StdDevMeanChkLineEdit.setToolTip('Standard deviation of the mean of the bridge voltage difference calculated from the _bvd.txt file')
        self.StdDevMeanPPMLineEdit.setToolTip('Standard deviation of the bridge voltage difference calculated from the raw .txt file')
        self.StdDevMeanPPMLineEdit.setToolTip('Standard deviation of the mean of the bridge voltage difference calculated from the raw .txt file')
        self.StdDevC1LineEdit.setToolTip('Standard deviation of C<sub>1</sub>')
        self.StdDevC2LineEdit.setToolTip('Standard deviation of C<sub>2</sub>')
        self.R1STPLineEdit.setToolTip('Value of the primary resistor at standard temperature and pressure')
        self.R2STPLineEdit.setToolTip('Value of the secondary resistor at standard temperature and pressure')
        self.NLineEdit.setToolTip('Total number of measurements or total number of full cycles')
        self.StdDevPPMLineEdit.setToolTip('Standard deviation of the resistance calculated from the raw .txt file')
        self.StdDevChkPPMLineEdit.setToolTip('Standard deviation of the resistance calculated from the _bvd.txt file')
        self.ppmMeanLineEdit.setToolTip('Mean resistance value calculated from the raw .txt file')
        self.RMeanChkPPMLineEdit.setToolTip('Mean resistance value calculated from the _bvd.txt file')
        self.RatioMeanLineEdit.setToolTip('Mean of the Ratio  R<sub>1</sub>/R<sub>2</sub>')
        self.le_ratioStdMean.setToolTip('Standard deviation of the mean of the Ratio R<sub>1</sub>/R<sub>2</sub>')
        self.IgnoredFirstLineEdit.setToolTip('Set the number of ignored first mesurements in every half cycle')
        self.IgnoredLastLineEdit.setToolTip('Set the number of ignored last mesurements in every half cycle')
        self.le_error.setToolTip('R Mean - R Mean Chk')
        self.C1C2LineEdit.setToolTip('Difference between C<sub>1</sub> and C<sub>2</sub>')
        self.MagElecComboBox.setToolTip('S/N of the CCCDrive')
        self.ProbeComboBox.setToolTip('Type or S/N of probe')
        self.R1OilDepthSpinBox.setToolTip('Set the oil depth of the primary resistor')
        self.R2OilDepthSpinBox.setToolTip('Set the oil depth of the secondary resistor')
        self.folderToolButton.setToolTip('Select the _bvd.txt file to load')
        self.btn_temperature1.setToolTip('Select the folder for the primary resistors environment')
        self.btn_temperature2.setToolTip('Select the folder for the secondary resistors environment')
        self.SquidFeedBut.setToolTip('Sets the SQUID feedback polarity')
        self.CurrentBut.setToolTip('Set which side/arm the SQUID feedback is applied')
        self.StandardRBut.setToolTip('Set the primary or secondary resistor as standard')
        self.MDSSButton.setToolTip('Click to save pipe seperated results file')
        self.saveButton.setToolTip('Save a pipe seperated results file')
        self.chb_outlier.setToolTip('Check to remove BVD values that are more than 3 sigma from the mean')
        self.lbl_cnOutput_rbv.setToolTip('Compensation output')
    
    def show_warning_dialog(self):
        # Calculate center of main window
        self.msgBox.setText(self.user_warn_msg)
        parent_rect = mainWindow.frameGeometry()
        center_point = parent_rect.center()

        # Calculate position for the message box
        self.msgBox_rect = self.msgBox.frameGeometry()
        x = int(center_point.x() - self.msgBox_rect.width() / 2)
        y = int(center_point.y() - self.msgBox_rect.height() / 2)

        self.msgBox.show()
        self.msgBox.move(x, y)
        response = self.msgBox.exec()
        return response
        
    def CCCDiagramTabSetUp(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.CCCDiagramTab = QWidget()
        self.tabWidget.addTab(self.CCCDiagramTab, "")
        self.VerticalLayoutWidget = QWidget(parent=self.CCCDiagramTab)
        self.VerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH-125, 691))
        self.VerticalLayout = QVBoxLayout(self.VerticalLayoutWidget)
        self.lbl_cccdiagram = QLabel(parent=self.CCCDiagramTab)
        self.lbl_cccdiagram.setGeometry(QRect(0, 5, winSizeH-125, winSizeV-75))
        self.lbl_cccdiagram.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mysp = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_cccdiagram.setSizePolicy(mysp)
        self.CCCDiagram()
    
    def CCCDiagram(self, R1="0", R2="0", N1="0", N2="0", I1="", I2="", BVD="", Na="1", RH="", RL="", Ia="") -> None:
        # Draw the circuit diagram
        # E 15 0 opamp 16 17 V; up, scale=0.3, size=0.4, color=red
        # W 6 16; right, color=red, size=0.3, scale=0.3
        # W 9 17; left, color=red, size=0.3, scale=0.3
        try:
            cct = Circuit("""
            I1 3 2; down, color=red, scale=0.5, l^={I_1}, i_>=""" + str(I1) + """
            W 3 4; down, steps=|-, free, color=red, size=1
            W 4 5; down, color=red, size=0.75
            R1 5 6; down=1, color=red,scale=0.5, l^={R_1}, a_=""" + str(R1) + """, label_style=split
            W 5 16; right, color=red, size=0.75
            R2 16 9; down, color=red, scale=0.5, l_={R_2}, a^=""" + str(R2) + """
            L2 9 10 {N_2}; down, mirror, color=blue, scale=0.5, size=1, l_={N_2}, a^=""" + str(N2) + """
            W 9 0; right=0.02, ground, color=red, label_nodes=none
            VM 6 9; right, scale=0.6, color=red, l_={\Delta{U}}, a^=""" + str(BVD) + """
            W 10 11; down, color=blue, size=1.25
            W 11 12; right, color=blue, size=0.75
            W 12 13; up, color=red, size=1.25
            I2 14 13 {I_2}; down, color=red, scale=0.5, l_={I_2}, i^>=""" + str(I2) + """,
            W 14 15; up, steps=|-, free, color=red, size=0.75
            W 15 16; down, color=red, size=0.75
            L1 6 7 {N_1}; down=1, color=blue, scale=0.5, size=0.5, l^={N_1}, a_=""" + str(N1) + """
            L3 7 8 {N_A}; down, color=blue, scale=0.5, size=1, l_={N_A}, i^={I_A}, a^=""" + str(Ia) + """
            R3 1 8; variable, right, color=red, scale=0.5, size=0.75, l^={R_H}, a_=""" + str(RH) + """, label_style=split
            R4 2 7; variable, right, color=red, scale=0.5, size=0.75, l^={R_L}, a_=""" + str(RL) + """, label_style=split
            W 1 2; up, color=red, size=1.25
            S1 circle; color=blue, size=0.4, l^={\phi}
            W 7 S1.mid; right, dotted, line width=0pt, size=0.5
            W 10 S1.mid; left, dotted, line width=0pt, size=0.5
            W S1.s 17; down, color=red, size=0.25, dashed, i={i_f}
            W 17 13; right, steps=-|, free, color=red, size=0.5, dashed, i={I_f}
            ;draw_nodes=connections, label_ids=false, label_nodes=none, label_style=aligned, dpi=600""")
            cct.draw(base_dir + r'\data\ccc_diagram.png', debug=2)
            plt.close('all')
            self.pixmap_cccdiagram = QPixmap(base_dir + r'\data\ccc_diagram.png')
            # Set the pixmap to the label
            scaled_pixmap = self.pixmap_cccdiagram.scaled(self.lbl_cccdiagram.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_cccdiagram.setPixmap(scaled_pixmap)
            # Resize the label to fit the image
            self.lbl_cccdiagram.setScaledContents(True)
            self.lbl_cccdiagram.show()
        except Exception as e:
            self.pixmap_cccdiagram = QPixmap(base_dir + r'\data\ccc_diagram_default.png')
            # Set the pixmap to the label
            scaled_pixmap = self.pixmap_cccdiagram.scaled(self.lbl_cccdiagram.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_cccdiagram.setPixmap(scaled_pixmap)
            # Resize the label to fit the image
            self.lbl_cccdiagram.setScaledContents(True)
            self.lbl_cccdiagram.show()
        
    def voltageTabSetUp(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        global winSizeH
        self.voltageTab = QWidget()
        self.tabWidget.addTab(self.voltageTab, "")
        self.voltageVerticalLayoutWidget = QWidget(parent=self.voltageTab)
        self.voltageVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH-125, 691))
        self.voltageVerticalLayout = QVBoxLayout(self.voltageVerticalLayoutWidget)
        self.raw_fig = plt.figure()
        self.raw_ax1 = self.raw_fig.add_subplot(2, 2, (1, 2))
        self.raw_ax2 = self.raw_fig.add_subplot(2, 2, 3)
        self.raw_ax3 = self.raw_fig.add_subplot(2, 2, 4)
        self.raw_fig.set_tight_layout(True)
        
        self.raw_ax1.tick_params(which='both', direction='in')
        self.raw_ax1.set_xlabel('Count')
        self.raw_ax1.set_ylabel('All Bridge Voltages [V]')
        self.raw_ax1.grid(axis='both')
        
        self.raw_ax2.tick_params(which='both', direction='in')
        self.raw_ax2.set_xlabel('Count')
        self.raw_ax2.set_ylabel('Average Bridge Voltages [V]')
        self.raw_ax2.grid(axis='both')
        
        self.raw_ax3.tick_params(which='both', direction='in')
        self.raw_ax3.set_xlabel('Count')
        self.raw_ax3.set_ylabel('Used Bridge Voltages [V]')
        self.raw_ax3.grid(axis='both')
        
        self.raw_canvas = FigureCanvas(self.raw_fig)
        self.voltageVerticalLayout.addWidget(NavigationToolbar(self.raw_canvas))
        self.voltageVerticalLayout.addWidget(self.raw_canvas)


    def BVDTabSetUp(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        global winSizeH
        self.BVDTab = QWidget()
        self.tabWidget.addTab(self.BVDTab, "")
        self.BVDVerticalLayoutWidget = QWidget(parent=self.BVDTab)
        self.BVDVerticalLayoutWidget.setGeometry(QRect(0, 0, winSizeH-125, 691))
        self.BVDVerticalLayout = QVBoxLayout(self.BVDVerticalLayoutWidget)
        self.BVDfig = plt.figure()
        # self.BVDax1 = self.BVDfig.add_subplot(2, 6, (4, 6))
        # self.BVDax4 = self.BVDfig.add_subplot(2, 6, (1, 3))
        self.BVDax2 = self.BVDfig.add_subplot(1, 8, (1, 6))
        self.BVDax3 = self.BVDfig.add_subplot(1, 8, (7, 8))
        self.BVDfig.set_tight_layout(True)

        # self.BVDax1.tick_params(which='both', direction='in')
        # self.BVDax1.set_xlabel('Count')
        # self.BVDax1.set_ylabel('Average Bridge Voltages [V]')
        # self.BVDax1.grid(axis='both')

        # self.BVDax4.tick_params(which='both', direction='in')
        # self.BVDax4.set_xlabel('Count')
        # self.BVDax4.set_ylabel('Bridge Voltages [V]')
        # self.BVDax4.grid(axis='both')

        self.BVDax2.tick_params(which='both', direction='in')
        self.BVDax2.set_xlabel('Count')
        self.BVDax2.tick_params(axis='y', colors='b')
        self.BVDax2.set_axisbelow(True)
        self.BVDax2.grid(axis='both', zorder=2, which='both')
        self.BVDax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.BVDax2.xaxis.set_minor_locator(MultipleLocator(2))
        box = self.BVDax2.get_position()
        self.BVDax2.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])

        self.BVDtwin2 = self.BVDax2.twinx()
        self.BVDtwin2.tick_params(axis='y', direction='in', colors='r')
        self.BVDtwin2.set_yticklabels([])
        self.BVDtwin2.set_axisbelow(True)
        self.BVDtwin2.grid(axis='x', zorder=2, which='both')

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
        self.chb_outlier = QCheckBox("Remove Outliers", parent=gridWidget)
        self.chb_outlier.setGeometry(QRect(self.col7x, int(self.coly*11.5), self.lbl_width, self.lbl_height))
        self.chb_outlier.setTristate(False)
        self.chb_outlier.setCheckState(Qt.CheckState.Unchecked)
        self.chb_outlier.stateChanged.connect(self.changedOutlier)
        # self.LogoLabelBVD = QLabel(parent=gridWidget)
        # self.LogoLabelBVD.setPixmap(self.LogoPixmap)
        # self.LogoLabelBVD.setGeometry(QRect(550, 700, 300, 76))
        Spacer1 = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        Spacer2 = QSpacerItem(600, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        grid.addWidget(self.deletePlotBut, 1, 1, 2, 1)
        grid.addWidget(self.plotCountCombo, 3, 1, 2, 1)
        grid.addItem(Spacer1, 1, 2)
        grid.addItem(Spacer1, 3, 2)
        grid.addWidget(self.RestoreBut, 1, 3, 2, 1)
        grid.addWidget(self.RePlotBut, 3, 3, 2, 1)
        grid.addWidget(self.chb_outlier, 1, 4, 2, 1)
        grid.addItem(Spacer2, 1, 4)
        grid.addItem(Spacer2, 3, 4)
        # grid.addWidget(self.LogoLabelBVD, 2, 5, 3, 2)
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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

        self.Allanax2.set_ylabel('\u03C3(\u03C4), ' + r'$C_{1}$' + ' and ' + r'$C_{2}$' + ' [V]')
        self.Allanax2.set_xlabel('\u03C4 [s]')
        self.Allanax2.set_yscale('log')
        self.Allanax2.set_xscale('log')
        self.Allanax2.grid(which='both')
        # self.Allanax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.Allanax2.xaxis.set_major_formatter(ScalarFormatter())

        self.Allanax3.set_ylabel('\u03C3(\u03C4), BV [V]')
        self.Allanax3.set_xlabel('\u03C4 [s]')
        self.Allanax3.set_yscale('log')
        self.Allanax3.set_xscale('log')
        self.Allanax3.grid(which='both')
        # self.Allanax3.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.Allanax3.xaxis.set_major_formatter(ScalarFormatter())

        self.Allanax4.set_ylabel('\u03C3(\u03C4), ' + r'$\overline{BV}$' + ' [V]')
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

        self.VarianceTypeComboBox = QComboBox(parent=self.AllanTab)
        self.VarianceTypeComboBox.setEditable(False)
        self.VarianceTypeComboBox.addItem('Allan')
        self.VarianceTypeComboBox.addItem('Hadamard')
        self.VarianceTypeComboBox.currentIndexChanged.connect(self.plotAdev)

        self.OverlappingComboBox = QComboBox(parent=self.AllanTab)
        self.OverlappingComboBox.setEditable(False)
        self.OverlappingComboBox.addItem('non-overlapping')
        self.OverlappingComboBox.addItem('overlapping')
        self.OverlappingComboBox.currentIndexChanged.connect(self.plotAdev)
        self.AllanHorizontalSpacer = QSpacerItem(600, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # self.LogoLabelAllan = QLabel(parent=self.AllanTab)
        # self.LogoLabelAllan.setPixmap(self.LogoPixmap)
        # self.LogoLabelAllan.setGeometry(QRect(550, 700, 300, 76))

        self.AllanHorizontalLayout.addWidget(self.VarianceTypeComboBox)
        self.AllanHorizontalLayout.addWidget(self.AllanTypeComboBox)
        self.AllanHorizontalLayout.addItem(self.AllanHorizontalSpacer)
        # self.AllanHorizontalLayout.addWidget(self.LogoLabelAllan)
        self.AllanHorizontalLayout.addWidget(self.OverlappingComboBox)
        self.AllanVerticalLayout.addLayout(self.AllanHorizontalLayout)

    def SpecTabSetUp(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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

        lbl_lag_bva = QLabel('Lag of I-', parent=gridWidget)
        self.le_lag_bva = QLineEdit(gridWidget)
        self.le_lag_bva.setReadOnly(True)
        self.le_lag_bva.setFixedWidth(100)
        self.le_lag_bva.setFixedHeight(18)
        self.le_lag_bva.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_alpha_bva = QLabel('Alpha [I-]', parent=gridWidget)
        self.le_alpha_bva= QLineEdit(gridWidget)
        self.le_alpha_bva.setReadOnly(True)
        self.le_alpha_bva.setFixedWidth(130)
        self.le_alpha_bva.setFixedHeight(18)
        self.le_alpha_bva.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_lag_bvb = QLabel('Lag of I+', parent=gridWidget)
        self.le_lag_bvb = QLineEdit(gridWidget)
        self.le_lag_bvb.setReadOnly(True)
        self.le_lag_bvb.setFixedWidth(100)
        self.le_lag_bvb.setFixedHeight(18)
        self.le_lag_bvb.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: black}""")

        lbl_alpha_bvb = QLabel('Alpha [I+]', parent=gridWidget)
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
        global red_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.folderToolButton = QToolButton(parent=self.SetResTab)
        self.folderToolButton.setGeometry(QRect(self.col3x - 48, self.coly*10 + 30, 40, self.lbl_height))
        self.folderToolButton.setIcon(QIcon(base_dir + r'\icons\folder.ico'))
        self.folderToolButton.clicked.connect(self.folderClicked)

        self.btn_temperature1 = QToolButton(parent=self.SetResTab)
        self.btn_temperature1.setGeometry(QRect(self.col3x - 48, self.coly*11 + 30, 40, self.lbl_height))
        self.btn_temperature1.setIcon(QIcon(base_dir + r'\icons\folder.ico'))
        self.btn_temperature1.clicked.connect(self.get_temperature1)

        self.btn_temperature2 = QToolButton(parent=self.SetResTab)
        self.btn_temperature2.setGeometry(QRect(self.col3x - 48, self.coly*12 + 30, 40, self.lbl_height))
        self.btn_temperature2.setIcon(QIcon(base_dir + r'\icons\folder.ico'))
        self.btn_temperature2.clicked.connect(self.get_temperature2)

        self.SquidFeedBut = QPushButton(parent=self.SetResTab)
        self.SquidFeedBut.setGeometry(QRect(self.col3x, self.coly*11 + 25, self.lbl_width, int(self.lbl_height*1.2)))
        self.SquidFeedBut.setStyleSheet(blue_style)
        self.SquidFeedBut.clicked.connect(self.SquidButClicked)
        self.CurrentBut = QPushButton(parent=self.SetResTab)
        self.CurrentBut.setGeometry(QRect(self.col3x, self.coly*12 + 25, self.lbl_width, int(self.lbl_height*1.2)))
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.R1OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R1OilDepthSpinBox.setGeometry(QRect(self.col1x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1OilDepthSpinBox.setMaximum(1000)
        self.R1OilDepthSpinBox.valueChanged.connect(self.oilDepth1Changed)
        self.R2OilDepthSpinBox = QSpinBox(parent=self.SetResTab)
        self.R2OilDepthSpinBox.setGeometry(QRect(self.col1x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2OilDepthSpinBox.setMaximum(1000)
        self.R2OilDepthSpinBox.valueChanged.connect(self.oilDepth2Changed)

    def setComboBoxes(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.MagElecComboBox = QComboBox(parent=self.SetResTab)
        self.MagElecComboBox.setGeometry(QRect(self.col0x, self.coly*11 + 30, self.lbl_width, self.lbl_height))
        self.MagElecComboBox.setEditable(False)
        self.MagElecComboBox.addItem('CCC2014-01')
        self.MagElecComboBox.addItem('CCC2019-01')

        self.ProbeComboBox = QComboBox(parent=self.SetResTab)
        self.ProbeComboBox.setGeometry(QRect(self.col0x, self.coly*12 + 30, self.lbl_width, self.lbl_height))
        self.ProbeComboBox.setEditable(False)
        self.ProbeComboBox.addItem('Magnicon1')
        self.ProbeComboBox.addItem('NIST1')

    def setMisc(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.SetResDivider = QFrame(parent=self.SetResTab)
        self.SetResDivider.setGeometry(QRect(self.col3x + self.lbl_width + 10, -10, 20, winSizeV))
        self.SetResDivider.setFrameShape(QFrame.Shape.VLine)
        self.SetResDivider.setFrameShadow(QFrame.Shadow.Sunken)

        self.CommentsTextBrowser = QTextBrowser(parent=self.SetResTab)
        self.CommentsTextBrowser.setGeometry(QRect(self.col0x, self.coly*9 + 30, int(self.lbl_width*3.2), self.lbl_height*2))
        self.CommentsTextBrowser.setReadOnly(False)

        # self.progressBar = QProgressBar(parent=self.centralwidget)
        # self.progressBar.setGeometry(QRect(self.col7x, self.coly*4, self.lbl_width, self.lbl_height))
        # self.progressBar.setProperty("value", 0)

    def retranslateUi(self, mainWindow) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
        self.lbl_calmode.setText(_translate("mainWindow", "Cal. mode"))
        self.kLabel.setText(_translate("mainWindow", "k [Turns]"))
        self.SquidFeedLabel.setText(_translate("mainWindow", "SQUID Feedin Polarity"))
        self.StandardRBut.setText(_translate("mainWindow", self.RButStatus))
        self.R1TotalPresLabel.setText(_translate("mainWindow", "R<sub>1</sub> Total Pres. [Pa]"))
        self.VMeanLabel.setText(_translate("mainWindow", "Mean [V]"))
        self.RMeanChkPPMLabel.setText(_translate("mainWindow", f"R Mean Chk [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.C2Label.setText(_translate("mainWindow", f"C<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevMeanLabel.setText(_translate("mainWindow", "Std. Mean [V]"))
        self.R1STPLabel.setText(_translate("mainWindow", f"R1STPPred [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.R2STPLabel.setText(_translate("mainWindow", f"R2STPPred [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.C1Label.setText(_translate("mainWindow", f"C<sub>1</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevC2Label.setText(_translate("mainWindow", f"Std Dev C<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevC1Label.setText(_translate("mainWindow", f"Std Dev C<sub>1</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.RatioMeanLabel.setText(_translate("mainWindow", "Ratio Mean"))
        self.lbl_ratioStdMean.setText(_translate("mainWindow", "Ratio Std. Mean"))
        self.ppmMeanLabel.setText(_translate("mainWindow", f"Mean [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.C1C2Label.setText(_translate("mainWindow", f"C<sub>1</sub>-C<sub>2</sub> [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevPPM2Label.setText(_translate("mainWindow", f"Std. Dev [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevMeanPPMLabel.setText(_translate("mainWindow", f"Std. Mean [{chr(956)}{chr(937)}/{chr(937)}]"))
        self.StdDevLabel.setText(_translate("mainWindow", "Std. Dev. [V]"))
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
        self.lbl_path_temperature1.setText(_translate("mainWindow", 'R<sub>1</sub> Environment Path'))
        self.lbl_path_temperature2.setText(_translate("mainWindow", 'R<sub>2</sub> Environment Path'))
        self.R1ValueLabel.setText(_translate("mainWindow", f"R<sub>1</sub> Value [{chr(937)}]"))
        self.AppVoltLabel.setText(_translate("mainWindow", "Applied Voltage"))
        self.MeasLabel.setText(_translate("mainWindow", "Meas [s]"))
        self.DelayLabel.setText(_translate("mainWindow", "Delay [s]"))
        self.IgnoredFirstLabel.setText(_translate("mainWindow", "Ignored First"))
        self.IgnoredLastLabel.setText(_translate("mainWindow", "Ignored Last"))
        self.lbl_error.setText(_translate("mainWindow", f"Error [n{chr(937)}/{chr(937)}]"))
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
        self.lbl_start_time.setText(_translate("mainWindow", "Start time"))
        self.lbl_cnOutput.setText(_translate("mainWindow", "CN Output"))
        self.lbl_end_time.setText(_translate("mainWindow", "End time"))
        self.lbl_range_shunt.setText(_translate("mainWindow", "Range shunt"))
        self.lbl_12bitdac.setText(_translate("mainWindow", "12 bit DAC/16 Bit DAC"))
        self.CurrentBut.setText(_translate("mainWindow", self.CurrentButStatus))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.CCCDiagramTab), _translate("mainWindow", "Diagram"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.voltageTab), _translate("mainWindow", "BV"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.BVDTab), _translate("mainWindow", "BVD"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.AllanTab), _translate("mainWindow", "Allan Dev."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SpecTab), _translate("mainWindow", "Power Spec."))
        self.txtFileLabel.setText(_translate("mainWindow", ".txt file"))
        self.VMeanChkLabel.setText(_translate("mainWindow", "Mean Chk [V]"))
        self.StdDevChkLabel.setText(_translate("mainWindow", "Std. Dev. Chk [V]"))
        self.StdDevMeanChkLabel.setText(_translate("mainWindow", "Std. Mean Chk [V]"))
        self.saveButton.setText(_translate("mainWindow", "Save"))
        self.MDSSButton.setText(_translate("mainWindow", "No"))
        self.MDSSLabel.setText(_translate("mainWindow", "Save MDSS"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.SetResTab), _translate("mainWindow", "Settings/Results"))
    
    
    def plotRaw(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.AA_used_2d = []
        self.BB_used_2d = []
        aa_used_len = len(self.AA_used[0])
        bb_used_len = len(self.BB_used[0])
        if self.bvd_stat_obj is not None:
            for i in self.AA_used:
                # print(len(i), aa_used_len)
                if len(i) != aa_used_len:
                    pass
                else:
                    self.AA_used_2d.append(i)
            for i in self.BB_used:
                if len(i) != bb_used_len:
                    pass
                else:
                    self.BB_used_2d.append(i)
            aa_2d = array(self.AA_used_2d).flatten().tolist()
            bb_2d = array(self.BB_used_2d).flatten().tolist()
            
            count_aa_2D = linspace(0, len(aa_2d)-1, num=len(aa_2d))
            count_bb_2D = linspace(0, len(bb_2d)-1, num=len(bb_2d))
            count_a = linspace(0, len(self.A)-1, num=len(self.A))
            count_b = linspace(0, len(self.B)-1, num=len(self.B))
            count_aa = linspace(0, len(self.AA)-1, num=len(self.AA))
            count_bb = linspace(0, len(self.BB)-1, num=len(self.BB))
            
            # print(len(count_aa_2D), len(count_bb_2D))
            # print(len(aa_2d), len(bb_2d))
            if self.plottedRaw:
                self.clearRawPlot()
                # print(len(count_a), len(self.A))
                # print(len(count_b), len(self.B))
                self.raw_ax1_ref[0].set_data(count_aa_2D, aa_2d)
                self.raw_ax12_ref[0].set_data(count_bb_2D, bb_2d)
                
                self.raw_ax2_ref[0].set_data(count_a, self.A)
                self.raw_ax22_ref[0].set_data(count_b, self.B)
                
                self.raw_ax3_ref[0].set_data(count_aa, self.AA)
                self.raw_ax32_ref[0].set_data(count_bb, self.BB)
            else:
                self.raw_ax1_ref = self.raw_ax1.errorbar(count_aa_2D, aa_2d, marker='o', ms=3, mfc='blue', mec='blue', ls='--', lw=1.0, alpha=self.alpha, label=r'All $I-$')
                self.raw_ax12_ref = self.raw_ax1.errorbar(count_bb_2D, bb_2d, marker='o', ms=3, mfc='red', mec='red', ls='--', lw=1.0,  alpha=self.alpha, label=r'All $I+$')
                self.raw_ax1.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', frameon=True, shadow=True, ncols=2, columnspacing=0)
                
                self.raw_ax2_ref = self.raw_ax2.errorbar(count_a, self.A, marker='o', ms=3, mfc='blue', mec='blue', ls='', alpha=self.alpha, label=r'$\overline{I-}$')
                self.raw_ax22_ref = self.raw_ax2.errorbar(count_b, self.B, marker='o', ms=3, mfc='red', mec='red', ls='', alpha=self.alpha, label=r'$\overline{I+}$')
                self.raw_ax2.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', frameon=True, shadow=True, ncols=2, columnspacing=0)

                self.raw_ax3_ref = self.raw_ax3.errorbar(count_aa, self.AA, marker='o', ms=3, mfc='blue', mec='blue', ls='', alpha=self.alpha, label=r'$I-$')
                self.raw_ax32_ref = self.raw_ax3.errorbar(count_bb, self.BB, marker='o', ms=3, mfc='red', mec='red', ls='', alpha=self.alpha, label=r'$I+$')
                self.raw_ax3.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', frameon=True, shadow=True, ncols=2, columnspacing=0)

            self.raw_ax1.relim()
            self.raw_ax1.autoscale(tight=None, axis='both', enable=True)
            self.raw_ax1.autoscale_view(tight=None, scalex=True, scaley=True)
            
            self.raw_ax2.relim()
            self.raw_ax2.autoscale(tight=None, axis='both', enable=True)
            self.raw_ax2.autoscale_view(tight=None, scalex=True, scaley=True)
            
            self.raw_ax3.relim()
            self.raw_ax3.autoscale(tight=None, axis='both', enable=True)
            self.raw_ax3.autoscale_view(tight=None, scalex=True, scaley=True)

            self.raw_canvas.draw()
            self.raw_canvas.flush_events()
            self.raw_fig.set_tight_layout(True)
            self.plottedRaw = True

    def plotBVD(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.bvd_stat_obj is not None:
            # count_a = linspace(0, len(self.A)-1, num=len(self.A))
            # count_b = linspace(0, len(self.B)-1, num=len(self.B))
            # count_aa = linspace(0, len(self.AA)-1, num=len(self.AA))
            # count_bb = linspace(0, len(self.BB)-1, num=len(self.BB))
            if self.corr_bvdList:
                BVDmean = mean(self.corr_bvdList)
                BVDstd  = std(self.corr_bvdList, ddof=1)
                upper   =  3*BVDstd + BVDmean
                lower   = -3*BVDstd + BVDmean
                if self.plottedBVD:
                    self.clearBVDPlot()
                    # self.BVDax1_ref[0].set_data(count_a, self.A)
                    # self.BVDax12_ref[0].set_data(count_b, self.B)
                    # self.BVDax41_ref[0].set_data(count_aa, self.AA)
                    # self.BVDax42_ref[0].set_data(count_bb, self.BB)
                    if self.RButStatus == 'R1':
                        self.BVDax21_ref[0].set_data(self.bvdCount, self.R1List)
                    else:
                        self.BVDax21_ref[0].set_data(self.bvdCount, self.R2List)
                    self.BVDtwin21_ref[0].set_data(self.bvdCount, self.corr_bvdList)
                    self.BVDtwin22_ref[0].set_data(self.bvdCount, upper*ones(len(self.corr_bvdList), dtype=int))
                    self.BVDtwin23_ref[0].set_data(self.bvdCount, lower*ones(len(self.corr_bvdList), dtype=int))
                    self.BVDax3.hist(self.corr_bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                    self.BVDax3.set_ylim([self.BVDtwin2.get_ylim()[0], self.BVDtwin2.get_ylim()[1]])
                else:
                    # plot the individual bridge voltages
                    # self.BVDax1_ref = self.BVDax1.errorbar(count_a, self.A, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label=r'$\overline{I-}$')
                    # self.BVDax12_ref = self.BVDax1.errorbar(count_b, self.B, marker='o', ms=6, mfc='red', mec='red', ls='', alpha=self.alpha, label=r'$\overline{I+}$')
                    # self.BVDax1.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', frameon=True, shadow=True, ncols=2, columnspacing=0)

                    # self.BVDax41_ref = self.BVDax4.errorbar(count_aa, self.AA, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label=r'$I-$')
                    # self.BVDax42_ref = self.BVDax4.errorbar(count_bb, self.BB, marker='o', ms=6, mfc='red', mec='red', ls='', alpha=self.alpha, label=r'$I+$')
                    # self.BVDax4.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower right', frameon=True, shadow=True, ncols=2, columnspacing=0)
                    if self.RButStatus == 'R1':
                        self.BVDax21_ref = self.BVDax2.plot(self.bvdCount, self.R1List, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label= 'Resistance')
                    else:
                        self.BVDax21_ref = self.BVDax2.plot(self.bvdCount, self.R2List, marker='o', ms=6, mfc='blue', mec='blue', ls='', alpha=self.alpha, label= 'Resistance')
                    self.BVDtwin21_ref = self.BVDtwin2.plot(self.bvdCount, self.corr_bvdList, marker='o', ms=6, mfc='red', mec='red', ls='', alpha=self.alpha, label= 'BVD [V]')
                    self.BVDtwin22_ref = self.BVDtwin2.plot(self.bvdCount, upper*ones(len(self.corr_bvdList), dtype=int), marker='', color='red', ms=0, ls='--', alpha=self.alpha)
                    self.BVDtwin23_ref = self.BVDtwin2.plot(self.bvdCount, lower*ones(len(self.corr_bvdList), dtype=int), marker='', color='red', ms=0, ls='--', alpha=self.alpha)

                    self.BVDax3.hist(self.corr_bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                    self.BVDax3.set_ylim([self.BVDtwin2.get_ylim()[0], self.BVDtwin2.get_ylim()[1]])
                # Put a legend below current axis
                lines, labels   = self.BVDax2.get_legend_handles_labels()
                lines2, labels2 = self.BVDtwin2.get_legend_handles_labels()
                self.BVDax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.2),
                                   fancybox=True, shadow=True, ncols=2, columnspacing=0)
                if self.RButStatus == 'R1':
                    self.BVDax2.set_ylabel(r'$R_{2}$' + f' [{chr(956)}{chr(937)}/{chr(937)}]', color='b')
                else:
                    self.BVDax2.set_ylabel(r'$R_{1}$' + f' [{chr(956)}{chr(937)}/{chr(937)}]', color='b')
                # self.BVDax1.relim()
                # self.BVDax1.autoscale(tight=None, axis='both', enable=True)
                # self.BVDax1.autoscale_view(tight=None, scalex=True, scaley=True)
                # self.BVDax4.relim()
                # self.BVDax4.autoscale(tight=None, axis='both', enable=True)
                # self.BVDax4.autoscale_view(tight=None, scalex=True, scaley=True)
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
                self.SkewnessEdit.setText(str("{:.3f}".format(mystat.skewness(self.corr_bvdList))))
                self.KurtosisEdit.setText(str("{:.3f}".format(mystat.kurtosis(self.corr_bvdList))))
                self.plottedBVD = True

    def changedR1STPPred(self,):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.changedR1STPBool = True
        self.R1STP = float(self.R1STPLineEdit.text())
        self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        self.setValidData()
        self.plotBVD()

    def changedR2STPPred(self,):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.changedR2STPBool = True
        self.R2STP = float(self.R2STPLineEdit.text())
        self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        self.setValidData()
        self.plotBVD()
        return

    def changedDeltaI2R2(self, ):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if float(self.le_deltaI2R2.text()) != 0.0:
            self.cleanUp()
            self.changedDeltaI2R2Ct = 1
            self.getBVD()
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()

    # def changedSamplesUsed(self, ):
    #     if debug_mode:
    #         logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
    #     if int(self.SampUsedLineEdit.text()) != 0 and int(self.SampUsedLineEdit.text()) <= int(self.dat.SHC) and int(self.SampUsedLineEdit.text())%2 == 0:
    #         self.cleanUp()
    #         self.SampUsedCt = 1
    #         self.getBVD()
    #         self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
    #         self.setValidData()
    #         self.plotBVD()
    #         self.plotStatMeasures()
    
    def changedOutlier(self, state):
        self.outlierPressed = True
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if state == 2:
            self.outliers = True
        else:
            self.outliers = False
        self.cleanUp()
        self.getBVD()
        self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        self.setValidData()
        self.plotBVD()
        self.plotStatMeasures()

    def changedIgnoredFirst(self, ):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if int(self.IgnoredFirstLineEdit.text()) <= int(self.dat.SHC) and int(self.IgnoredFirstLineEdit.text())%2 == 0:
            self.cleanUp()
            self.SampUsedCt = 1
            self.getBVD()
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()
            self.plotStatMeasures()

    def changedIgnoredLast(self, ):
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if int(self.IgnoredLastLineEdit.text()) <= int(self.dat.SHC) and int(self.IgnoredLastLineEdit.text())%2 == 0:
            self.cleanUp()
            self.SampUsedCt = 1
            self.getBVD()
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()
            self.plotStatMeasures()

    def is_overlapping(self, overlapping: str) -> bool:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if overlapping == 'overlapping':
            return True
        else:
            return False

    def powers_of_2(self, n: int) -> list:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        x   = 1
        arr = []
        while(x < n):
            arr.append(x)
            x = x*2
        return arr

    def plotAllan(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.corr_bvdList != []:
            if self.AllanTypeComboBox.currentText() == '2^n (octave)':
                # tau_list = self.powers_of_2(int(len(self.corr_bvdList)//2))
                mytaus = 'octave'
            elif self.AllanTypeComboBox.currentText() == 'all':
                # tau_list = list(map(int, linspace(1, len(self.corr_bvdList)//2, len(self.corr_bvdList)//2)))
                mytaus = 'all'
            # tau list is same for all...
            # tau_list_C1 = tau_list
            # tau_list_C2 = tau_list
            # tau_list_bva = tau_list
            # tau_list_bvb = tau_list
            # bvd_tau, bvd_adev_ali, bvd_aerr = mystat.adev(array(self.bvdList), self.overlapping, tau_list)
            # C1_tau, C1_adev, C1_aerr = mystat.adev(array(self.V1), self.overlapping, tau_list_C1)
            # C2_tau, C2_adev, C2_aerr = mystat.adev(array(self.V2), self.overlapping, tau_list_C2)
            # bva_tau, bva_adev, bva_aerr = mystat.adev(array(self.A), self.overlapping, tau_list_bva)
            # bvb_tau, bvb_adev, bvb_aerr = mystat.adev(array(self.B), self.overlapping, tau_list_bvb)
            # using allantools because it is faster than O(n^2)
            # print(self.dat.intTime, self.dat.timeBase)
            # print("sampling times: ", self.dat.fullCyc, self.dat.intTime/self.dat.timeBase, self.dat.dt )
            try:
                if self.overlapping:
                    if self.VarianceTypeComboBox.currentText() == 'Allan':
                        (bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn) = allantools.oadev(array(self.corr_bvdList), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (C1_tau, C1_adev, C1_aerr, C1_adn) = allantools.oadev(array(self.V1), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (C2_tau, C2_adev, C2_aerr, C2_adn) = allantools.oadev(array(self.V2), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (aa_tau_time, aa_adev, aa_aerr, aa_adn) = allantools.oadev(array(self.AA), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bb_tau_time, bb_adev, bb_aerr, bb_adn) = allantools.oadev(array(self.BB), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bva_tau_time, bva_adev, bva_aerr, bva_adn) = allantools.oadev(array(self.A), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                        (bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn) = allantools.oadev(array(self.B), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                    elif self.VarianceTypeComboBox.currentText() == 'Hadamard':
                        (bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn) = allantools.ohdev(array(self.corr_bvdList), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (C1_tau, C1_adev, C1_aerr, C1_adn) = allantools.ohdev(array(self.V1), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (C2_tau, C2_adev, C2_aerr, C2_adn) = allantools.ohdev(array(self.V2), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (aa_tau_time, aa_adev, aa_aerr, aa_adn) = allantools.ohdev(array(self.AA), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bb_tau_time, bb_adev, bb_aerr, bb_adn) = allantools.ohdev(array(self.BB), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bva_tau_time, bva_adev, bva_aerr, bva_adn) = allantools.ohdev(array(self.A), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                        (bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn) = allantools.ohdev(array(self.B), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                else:
                    if self.VarianceTypeComboBox.currentText() == 'Allan':
                        (bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn) = allantools.adev(array(self.corr_bvdList), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)  # Compute the overlapping ADEV
                        (C1_tau, C1_adev, C1_aerr, C1_adn) = allantools.adev(array(self.V1), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (C2_tau, C2_adev, C2_aerr, C2_adn) = allantools.adev(array(self.V2), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (aa_tau_time, aa_adev, aa_aerr, aa_adn) = allantools.adev(array(self.AA), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bb_tau_time, bb_adev, bb_aerr, bb_adn) = allantools.adev(array(self.BB), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bva_tau_time, bva_adev, bva_aerr, bva_adn) = allantools.adev(array(self.A), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                        (bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn) = allantools.adev(array(self.B), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                    elif self.VarianceTypeComboBox.currentText() == 'Hadamard':
                        (bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn) = allantools.hdev(array(self.corr_bvdList), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)  # Compute the overlapping ADEV
                        (C1_tau, C1_adev, C1_aerr, C1_adn) = allantools.hdev(array(self.V1), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (C2_tau, C2_adev, C2_aerr, C2_adn) = allantools.hdev(array(self.V2), rate=1./self.dat.fullCyc, data_type="freq", taus=mytaus)
                        (aa_tau_time, aa_adev, aa_aerr, aa_adn) = allantools.hdev(array(self.AA), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bb_tau_time, bb_adev, bb_aerr, bb_adn) = allantools.hdev(array(self.BB), rate=1./(self.dat.intTime/self.dat.timeBase), data_type="freq", taus=mytaus)
                        (bva_tau_time, bva_adev, bva_aerr, bva_adn) = allantools.hdev(array(self.A), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
                        (bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn) = allantools.hdev(array(self.B), rate=1./self.dat.dt, data_type="freq", taus=mytaus)
            except Exception as e:
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + ' Error: ' + str(e))
                bvd_tau_time, bvd_adev, bvd_aerr, bvd_adn,\
                C1_tau, C1_adev, C1_aerr, C1_adn, \
                C2_tau, C2_adev, C2_aerr, C2_adn, \
                aa_tau_time, aa_adev, aa_aerr, aa_adn, \
                bb_tau_time, bb_adev, bb_aerr, bb_adn, \
                bva_tau_time, bva_adev, bva_aerr, bva_adn, \
                bvb_tau_time, bvb_adev, bvb_aerr, bvb_adn  = ([] for _ in range(28))
                pass
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

            if self.plottedAllan:
                self.clearAllanPlot()
                self.Allanax1_ref[0].set_data(array(bvd_tau_time), array(bvd_adev))
                self.Allanax11_ref[0].set_data(array(bvd_tau_time), array(rttau))
                self.Allanax21_ref[0].set_data(array(C1_tau), array(C1_adev))
                self.Allanax22_ref[0].set_data(array(C2_tau), array(C2_adev))
                self.Allanax31_ref[0].set_data(array(aa_tau_time), array(aa_adev))
                self.Allanax32_ref[0].set_data(array(bb_tau_time), array(bb_adev))
                self.Allanax41_ref[0].set_data(array(bva_tau_time), array(bva_adev))
                self.Allanax42_ref[0].set_data(array(bvb_tau_time), array(bvb_adev))
            else:
                self.Allanax1_ref = self.Allanax1.plot(bvd_tau_time, bvd_adev, 'ko-', lw=1.25, ms=4, alpha = self.alpha) # ADev for BVD
                self.Allanax11_ref = self.Allanax1.plot(bvd_tau_time,  rttau, 'r', lw = 2, alpha=self.alpha-0.1, label=r'$1/\sqrt{\tau}$') # white noise fit
                self.Allanax21_ref = self.Allanax2.plot(C1_tau, C1_adev, 'go-', lw=1.25, ms=4, alpha = self.alpha, label=r'$C_{1}$') # ADev for C1
                self.Allanax22_ref = self.Allanax2.plot(C2_tau, C2_adev, 'yo-', lw=1.25, ms=4, alpha=self.alpha, label=r'$C_{2}$') # ADev for C2
                self.Allanax31_ref = self.Allanax3.plot(aa_tau_time, aa_adev, 'bo-', lw=1.25, ms=4, alpha=self.alpha, label=r'$I-$')
                self.Allanax32_ref = self.Allanax3.plot(bb_tau_time, bb_adev, 'ro-', lw=1.25, ms=4, alpha=self.alpha, label=r'$I+$')
                self.Allanax41_ref = self.Allanax4.plot(bva_tau_time, bva_adev, 'bo-', lw=1.25, ms=4, alpha=self.alpha, label=r'$\overline{I-}$') # ADev for bv average(a)
                self.Allanax42_ref = self.Allanax4.plot(bvb_tau_time, bvb_adev, 'ro-', lw=1.25, ms=4, alpha=self.alpha, label=r'$\overline{I+}$') # ADev for bv average(b)
                self.plottedAllan = True

            with open(self.pathString + '_pyadev.txt', 'w') as adev_file:
                # Create header string
                adev_file.write('tau (s)' + '\t' + 'adev [BVD]' + '\t' + 'adev err [BVD]' + \
                                '\n')
            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                for i, j, k, in zip(bvd_tau_time, bvd_adev, bvd_aerr):
                    adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
                adev_file.write('\n')

            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                adev_file.write('tau (s)' + '\t' + 'adev [BV <I->]' + '\t' + 'adev err [BV <I->]' + \
                                '\n')
            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                for i, j, k, in zip(bva_tau_time, bva_adev, bva_aerr):
                    adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
                adev_file.write('\n')

            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                adev_file.write('tau (s)' + '\t' + 'adev [BV <I+>]' + '\t' + 'adev err [BV <I+>]' + \
                                '\n')
            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                for i, j, k, in zip(bvb_tau_time, bvb_adev, bvb_aerr):
                    adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
                adev_file.write('\n')

            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                adev_file.write('tau (s)' + '\t' + 'adev [BV I-]' + '\t' + 'adev err [BV I-]' + \
                                '\n')
            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                for i, j, k, in zip(aa_tau_time, aa_adev, aa_aerr):
                    adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
                adev_file.write('\n')

            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                adev_file.write('tau (s)' + '\t' + 'adev [BV I+]' + '\t' + 'adev err [BV I+]' + \
                                '\n')
            with open(self.pathString + '_pyadev.txt', 'a') as adev_file:
                for i, j, k, in zip(bb_tau_time, bb_adev, bb_aerr):
                    adev_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\n')
                adev_file.write('\n')

        self.Allanax1.legend(loc='upper right', frameon=True, shadow=True, ncols=1, columnspacing=0)
        self.Allanax1.relim()
        self.Allanax1.autoscale(tight=None, axis='both', enable=True)
        self.Allanax1.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax2.relim()
        self.Allanax2.autoscale(tight=None, axis='both', enable=True)
        self.Allanax2.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax2.legend(loc='best', frameon=True, shadow=True, ncols=2, columnspacing=1)
        self.Allanax3.relim()
        self.Allanax3.autoscale(tight=None, axis='both', enable=True)
        self.Allanax3.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax3.legend(loc='best', frameon=True, shadow=True, ncols=2, columnspacing=1)
        self.Allanax4.relim()
        self.Allanax4.autoscale(tight=None, axis='both', enable=True)
        self.Allanax4.autoscale_view(tight=None, scalex=True, scaley=True)
        self.Allanax4.legend(loc='best', frameon=True, shadow=True, ncols=2, columnspacing=1)
        self.Allanfig.set_tight_layout(True)
        self.AllanCanvas.draw()

    def plotSpec(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        try:
            samp_freq = 1./(self.dat.fullCyc)
            # sig_freq = 1./(self.dat.fullCyc)
            # print("BVD Sampling frequency: ", samp_freq)
            # print("Measurement time: ", self.dat.measTime)
            # print("BV Sampling frequency: ", self.dat.dt)
            # Create the window function
            freq_bvd, mypsd_bvd = signal.welch(array(self.corr_bvdList), fs=samp_freq, window='hann', \
                                             nperseg=len(self.corr_bvdList), scaling='density', \
                                             axis=-1, average='mean', return_onesided=True)
            freqA, mypsdA = signal.welch(array(self.A), fs=self.dat.dt, window='hann', \
                                             nperseg=len(self.A),  scaling='density', \
                                             axis=-1, average='mean', return_onesided=True)
            freqB, mypsdB = signal.welch(array(self.B), fs=self.dat.dt, window='hann', \
                                             nperseg=len(self.B),  scaling='density', \
                                             axis=-1, average='mean', return_onesided=True)
            self.h0 = mean(mypsd_bvd[1:])
            # print("Noise power BVD: ", mean(mypsd_bvd[1:]))
            # print("Noise power BVA: ", mean(mypsdA[1:]))
            # print("Noise power BVB: ", mean(mypsdB[1:]))

            # Ali's custom PSD calculation...[works but slower than scipy welch]
            # mywindow_mystat = mystat.hann(float(samp_freq), (len(self.bvdList)*float(samp_freq)))
            # freq_bvd, mypsa_bvd = mystat.calc_fft(1./(float(samp_freq)), array(self.bvdList), array(mywindow_mystat))
            lag_bvd, acf_bvd, pci_bvd, nci_bvd, cutoff_lag_bvd = mystat.autoCorrelation(array(self.corr_bvdList))
            lag_bva, acf_bva, pci_bva, nci_bva, cutoff_lag_bva = mystat.autoCorrelation(array(self.A))
            lag_bvb, acf_bvb, pci_bvb, nci_bvb, cutoff_lag_bvb = mystat.autoCorrelation(array(self.B))
            try:
                (pow_bvd, noise_bvd) = mystat.noise1D(array(self.corr_bvdList))
                (pow_bva, noise_bva) = mystat.noise1D(array(self.A))
                (pow_bvb, noise_bvb) = mystat.noise1D(array(self.B))
            except Exception as e:
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                (pow_bvd, noise_bvd) = ('', '')
                (pow_bva, noise_bva) = ('', '')
                (pow_bvb, noise_bvb) = ('', '')
                pass
        except Exception as e:
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + ' Error: ' + str(e))
            freq_bvd, mypsd_bvd, freqA, mypsdA, freqB, mypsdB, \
            lag_bvd, acf_bvd, pci_bvd, nci_bvd, \
            lag_bva, acf_bva, pci_bva, nci_bva, \
            lag_bvb, acf_bvb, pci_bvb, nci_bvb = ([] for _ in range(18))
            pass
        if self.plottedSpec:
            self.clearSpecPlot()
            self.SpecAx_ref[0].set_data(array(freq_bvd), array(mypsd_bvd))
            self.SpecAx_ref1[0].set_data(array(freq_bvd), mean(mypsd_bvd[1:])*ones(len(freq_bvd)))
            self.SpecAx_ref1[0].set_label(r'$h_0 = $' + str("{:2.2e}".format(self.h0)))
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
            self.SpecAx_ref1 = self.SpecAx.plot(freq_bvd, mean(mypsd_bvd[1:])*ones(len(freq_bvd)), 'r', lw=2, alpha=self.alpha-0.1, label=r'$h_0 = $' + str("{:2.2e}".format(self.h0)))
            # PSD of BVA and BVB
            self.specA_ref = self.specAB.plot(freqA, mypsdA, 'bo-', lw=1.25, ms=2, alpha=self.alpha, label=r'$I-$')
            self.specB_ref = self.specAB.plot(freqB, mypsdB, 'ro-', lw=1.25, ms=2, alpha=self.alpha, label=r'$I+$')
            # ACF of BVD
            self.acf_bvd_ref = self.acf_bvd.plot(lag_bvd[0:], acf_bvd[0:], 'ko-', lw=0.5, ms = 4, alpha=self.alpha)
            self.acf_bvd_ref1 = self.acf_bvd.plot(lag_bvd[0:], pci_bvd[0:], ':', lw=2, color='red')
            self.acf_bvd_ref2 = self.acf_bvd.plot(lag_bvd[0:], nci_bvd[0:], ':', lw=2, color='red')
            # ACF of BVA and BVB
            self.acf_bv_refa = self.acf_bv.plot(lag_bva[0:], acf_bva[0:], 'bo', ms=2, alpha=self.alpha, label=r'$I-$')
            self.acf_bv_refb = self.acf_bv.plot(lag_bvb[0:], acf_bvb[0:], 'ro', ms=2, alpha=self.alpha, label=r'$I+$')

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
            psd_file.write('f (Hz)' + '\t' + 'psd [BV I-]' + '\n')
        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            for i, j, in zip(freqA, mypsdA):
                psd_file.write(str(i) + '\t' + str(j) + '\n')
            psd_file.write('\n')

        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            psd_file.write('f (Hz)' + '\t' + 'psd [BV I+]' + '\n')
        with open(self.pathString + '_pypsd.txt', 'a') as psd_file:
            for i, j, in zip(freqB, mypsdB):
                psd_file.write(str(i) + '\t' + str(j) + '\n')
            psd_file.write('\n')

    def clearBVDPlot(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.plottedBVD:
            try:
                # self.BVDax1_ref[0].set_data(array([]), array([]))
                # self.BVDax12_ref[0].set_data(array([]), array([]))
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
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                pass
    
    def clearRawPlot(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.plottedRaw:
            try:
                self.raw_ax1_ref[0].set_data(array([]), array([]))
                self.raw_ax12_ref[0].set_data(array([]), array([]))
                self.raw_ax2_ref[0].set_data(array([]), array([]))
                self.raw_ax22_ref[0].set_data(array([]), array([]))
                self.raw_ax3_ref[0].set_data(array([]), array([]))
                self.raw_ax32_ref[0].set_data(array([]), array([]))
                # for container in self.raw_ax1.containers:
                #     container.remove()
            
            except Exception as e:
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                pass

    def clearAllanPlot(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.plottedAllan:
            try:
                 self.Allanax1_ref[0].set_data(array([]), array([]))
                 self.Allanax11_ref[0].set_data(array([]), array([]))
                 self.Allanax21_ref[0].set_data(array([]), array([]))
                 self.Allanax22_ref[0].set_data(array([]), array([]))
                 self.Allanax31_ref[0].set_data(array([]), array([]))
                 self.Allanax32_ref[0].set_data(array([]), array([]))
                 self.Allanax41_ref[0].set_data(array([]), array([]))
                 self.Allanax42_ref[0].set_data(array([]), array([]))
                 # self.Allanax1.clear()
                 # self.Allanax2.clear()
                 # self.Allanax3.clear()
                 # self.Allanax4.clear()
            except Exception as e:
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                pass

    def clearSpecPlot(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.plottedSpec:
            try:
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
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                pass

    def clearPlots(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.clearBVDPlot()
        self.clearRawPlot()
        self.clearAllanPlot()
        self.clearSpecPlot()

    def RButClicked(self) -> None:
        global red_style
        global green_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.StandardRBut.pressed and self.RButStatus == 'R1':
            self.RButStatus = 'R2'
            self.StandardRBut.setText('R2')
            self.StandardRBut.setStyleSheet(green_style)
            if self.validFile:
                self.stdR(self.RButStatus)
                # print("Standard is R2")
        else:
            self.RButStatus = 'R1'
            self.StandardRBut.setText('R1')
            self.StandardRBut.setStyleSheet(red_style)
            if self.validFile:
                self.stdR(self.RButStatus)
                # print("Standard is R1")
        self.plotBVD()

    def SquidButClicked(self) -> None:
        global red_style
        global blue_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.SquidFeedBut.pressed and self.SquidFeedStatus == 'NEG':
            self.SquidFeedStatus = 'POS'
            self.SquidFeedBut.setText('Positive')
            self.SquidFeedBut.setStyleSheet(red_style)
        else:
            self.SquidFeedStatus = 'NEG'
            self.SquidFeedBut.setText('Negative')
            self.SquidFeedBut.setStyleSheet(blue_style)

    def CurrentButClicked(self) -> None:
        global red_style
        global blue_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        getData_start = perf_counter()
        if self.txtFilePath.endswith('_bvd.txt') and os.path.exists(self.txtFilePath) and self.txtFilePath.split('_bvd.txt')[0][-1].isnumeric():
            self.txtFile = self.txtFilePath.split('/')[-1]
            self.pathString = self.txtFilePath.split('_bvd.txt')[0]
            self.dat = magnicon_ccc(self.txtFilePath, dbdir, site)
            
            # getFile_end = perf_counter() - getData_start
            # print("Time taken to read files: " +  str(getFile_end))
            if len(self.dat.bvd) > 0:
                self.validFile = True
            else:
                self.validFile = False
            # get the standard temperature for the two resistors if they exist
            try:
                if self.le_path_temperature1.text() != '':
                    env1_obj = env(self.le_path_temperature1.text(), self.dat.startDate, self.dat.endDate)
                    (self.R1Temp, self.R1pres) = env1_obj.calc_average()
                    self.R1TotPres = self.R1pres + self.R1OilPres
                else:
                    self.R1Temp = self.dat.R1stdTemp
                    self.R1pres = 101325
                if self.le_path_temperature2.text() != '':
                    env2_obj = env(self.le_path_temperature2.text(), self.dat.startDate, self.dat.endDate)
                    (self.R2Temp, self.R2pres) = env2_obj.calc_average()
                    # print(self.R2Temp, self.R2pres)
                    self.R2TotPres = self.R2pres + self.R2OilPres
                else:
                    self.R2Temp = self.dat.R2stdTemp
                    self.R2pres = 101325
            except Exception as e:
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                self.R1Temp = 25
                self.R2Temp = 25
                self.R1pres = 101325
                self.R2pres = 101325
                pass
            # self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))
            self.IgnoredFirstLineEdit.setText(str(self.dat.ignored_first))
            self.IgnoredLastLineEdit.setText(str(self.dat.ignored_last))
            self.cleanUp()
            # getResults_end = perf_counter() - getData_start
            # print("Time taken to get Results: " + str(getResults_end))
            if self.validFile:
                # getBVD_start = perf_counter()
                self.getBVD()
                # print("Time taken to get BVD data: ", perf_counter() - getBVD_start)
                # getBVD_end = perf_counter() - getData_start
                # print("Time taken to get BVD: " +  str(getBVD_end))
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotRaw()
                self.plotBVD()
                self.plotStatMeasures()
                # plotBVD_start = perf_counter()
                # self.plot_bvd_thread = Thread(target = self.plotBVD, daemon=True)
                # self.plot_bvd_thread.start()
                # self.plot_bvd_thread.join() # wait for the thread to finish
                # # self.plotBVD()
                # # print("Time taken to plot BVD data: ", perf_counter() - plotBVD_start)
                # # plotStat_start = perf_counter()
                # self.stats_thread = Thread(target=self.plotStatMeasures, daemon=True)
                # self.stats_thread.start()
                # self.stats_thread.join() # wait for the thread to finish
                if self.tabWidget.currentIndex() == 0:
                    try:
                        self.draw_thread = Thread(target = self.CCCDiagram, args=(round(self.dat.R1NomVal, 2), round(self.dat.R2NomVal, 2), \
                                        self.dat.N1, self.dat.N2, format(self.dat.I1, ".1e"), \
                                        format(self.dat.I2, ".1e"), format(self.dat.bvdMean, ".1e"), \
                                        self.dat.NA, "10k*" + str(self.dat.dac12), "10k/" + str(self.dat.rangeShunt), format(self.dat.I1*self.k, ".1e"),), daemon=True)
                        self.draw_thread.start()
                        self.draw_thread.join()
                        self.draw_flag = True
                    except Exception as e:
                        logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + ' Error: ' + str(e))
                        self.draw_flag == False
                        if self.draw_thread is not None:
                            self.draw_thread.join()
                        pass
                        
                # print("Time taken to plot allan and spectrum: ", perf_counter() - plotStat_start)
                # getPlot_end = perf_counter() - getData_start
                # print("Time taken to plot all data in GUI: ", str(getPlot_end))
                getData_end = perf_counter() - getData_start
                # print("Time taken to get and analyze data: " +  str(getData_end))
                self.statusbar.showMessage('Time taken to process and display data ' + str("{:2.2f}".format(getData_end)) + ' s', 5000)
                if self.user_warn_msg != "":
                    self.show_warning_dialog()
            else:
                if self.stats_thread is not None:
                    self.stats_thread.join()
                if self.plot_bvd_thread is not None:
                    self.plot_bvd_thread.join()
                self.setInvalidData()
                self.statusbar.showMessage('Invalid file selected...', 2000)
                # self.clearPlots()
        else:
            # self.clearPlots()
            self.setInvalidData()
            self.statusbar.showMessage('Invalid file! Filename should end in _bvd.txt', 5000)

    def plotStatMeasures(self,) -> None:
        # TODO: this needs to be in a QThread in a future release...
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.plotSpec()
        self.plotAdev()

    def plotAdev(self,) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.overlapping = self.is_overlapping(self.OverlappingComboBox.currentText())
        self.plotAllan()

    def getBVD(self,):
        """Calculates the BVD from the raw text file only.
        Returns
        -------
        None.
        """
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        try:
            self.removed = []
            self.bvd_stat_obj = bvd_stat(self.txtFilePath, int(self.IgnoredFirstLineEdit.text()), \
                                         int(self.IgnoredLastLineEdit.text()), self.dat, debug_mode)
            self.bvdList, self.V1, self.V2, self.A, self.B, self.stdA, self.stdB, self.AA, self.BB, self.stdbvdList, self.AA_used, self.BB_used = self.bvd_stat_obj.send_bvd_stats()
            if self.outliers:
                BVDmean = mean(self.bvdList)
                BVDstd  = std(self.bvdList, ddof=1)
                upper   =  3*BVDstd + BVDmean
                lower   = -3*BVDstd + BVDmean
                for i in self.bvdList:
                    if i < upper and i > lower:
                        self.corr_bvdList.append(i)
            else:
                self.corr_bvdList = self.bvdList
            for i in range(len(self.corr_bvdList)):
                self.bvdCount.append(i)
            self.bvd_stat_obj.clear_bvd_stats()
        except Exception as e:
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                           ' Error: ' + str(e))
            self.bvdList, self.V1, self.V2, self.A, self.B, self.stdA, self.stdB, self.AA, self.BB, self.stdbvdList, self.AA_used, self.BB_used = [], [], [], [], [], [], [], [], [], [], [], []
            self.corr_bvdList = self.bvdList
            pass
        
        if self.dat.bvd != []:
            # this comes from _bvd.txt files
            self.bvd_mean_chk       = mean(self.dat.bvd)
            self.bvd_std_chk        = std(self.dat.bvd, ddof=1)
            self.bvd_stdmean_chk    = self.bvd_std_chk/sqrt(len(self.dat.bvd))
            upper_chk   =  3*self.bvd_std_chk + self.bvd_mean_chk
            lower_chk   = -3*self.bvd_std_chk + self.bvd_mean_chk
            if self.outliers:
                for ct, i in enumerate(self.dat.bvd):
                    if i > lower_chk and i < upper_chk:
                        self.bvdList_chk.append(i)
                    else:
                        self.removed.append(ct)
                        self.deletedIndex.append(ct)
                        # print(ct, len(self.dat.bvd) - ct - 1)
                        self.plotCountCombo.removeItem(len(self.dat.bvd) - ct)
            elif not self.outliers:
                self.bvdList_chk = self.dat.bvd
                if self.removed != []:
                    for i in self.removed:
                        self.plotCountCombo.addItem(f'ct {len(self.dat.bvd) - i}')
        else:
            self.bvdList_chk = []
        # print(len(self.A), len(self.B))

    # Results from data
    def results(self, mag, T1: float, T2: float, P1: float, P2: float) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if mag.deltaNApN1 == '':
            self.k = 0
            # (mag.N1*2048*mag.rangeShunt)
        else:
            self.k     = mag.deltaNApN1/mag.NA # in turns
        # correction factor for R1 and R2 due to temperature and pressure
        R1corr     = (mag.R1alpha*(T1-mag.R1stdTemp) + mag.R1beta*(T1-mag.R1stdTemp)**2) + (mag.R1pcr*(P1-101325))/1000
        R2corr     = (mag.R2alpha*(T2-mag.R2stdTemp) + mag.R2beta*(T2-mag.R2stdTemp)**2) + (mag.R2pcr*(P2-101325))/1000
        # print('R1 and R2 Corr: ', R1corr, R2corr)
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

        self.ratioMeanList      = []
        self.ratioMeanStdList   = []
        self.R1List             = []
        self.R2List             = []
        ratioMeanC1             = []
        ratioMeanC2             = []
        self.C1R1List           = []
        self.C1R2List           = []
        self.C2R1List           = []
        self.C2R2List           = []
        if self.changedDeltaI2R2Ct != 0:
            myDeltaI2R2 = float(self.le_deltaI2R2.text())
        else:
            myDeltaI2R2 = float(mag.deltaI2R2)
        try:
            compensation = mag.N1/mag.N2 * (1 + (self.k*mag.NA/mag.N1))
        except ZeroDivisionError:
            compensation = 0
            pass
        for v1, v2, bvd, stdbvd in zip(self.V1, self.V2, self.corr_bvdList, self.stdbvdList):
            # This calculation is done using the bridge voltages i.e the raw text file
            try:
                self.ratioMeanList.append(compensation*(1 + (bvd/myDeltaI2R2)))
                self.ratioMeanStdList.append(compensation*stdbvd/myDeltaI2R2)
                ratioMeanC1.append(compensation*(1 + v1/myDeltaI2R2))
                ratioMeanC2.append(compensation*(1 + v2/myDeltaI2R2))
            except ZeroDivisionError:
                self.ratioMeanList.append(0)
                self.ratioMeanStdList.append(0)
                ratioMeanC1.append(0)
                ratioMeanC2.append(0)
                pass
        for rm, rmC1, rmC2 in zip(self.ratioMeanList, ratioMeanC1, ratioMeanC2):
            try:
                self.R1List.append(float(((((self.R1*(1./rm))/mag.R2NomVal) - 1) * 10**6) - R2corr)) # this is actually R2List
                self.C1R1List.append((self.R1/rmC1 - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
                self.C2R1List.append((self.R1/rmC2 - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
            except ZeroDivisionError:
                self.R1List.append(0)
                self.C1R1List.append(0)
                self.C2R1List.append(0)
                pass
            try:
                self.R2List.append(float(((((self.R2*rm)/mag.R1NomVal) - 1) * 10**6) - R1corr)) # this is actually R1List
                self.C1R2List.append((self.R2*rmC1 - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
                self.C2R2List.append((self.R2*rmC2 - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
            except ZeroDivisionError:
                self.R2List.append(0)
                self.C1R2List.append(0)
                self.C2R2List.append(0)
        # print(self.R1List, mean(self.R1List), len(self.R1List))
        if self.ratioMeanList != []:
            # self.ratioMean = compensation*(1 + (self.bvd_mean/myDeltaI2R2)) # calculated from raw bridge voltages
            self.ratioMean = mean(self.ratioMeanList)
            self.ratioStdMean = std(self.ratioMeanList, ddof=1)/sqrt(len(self.ratioMeanList))
            self.meanR1     = mean(self.R1List) # this is mean of R2
            # self.meanR1     = float(((((self.R1/mean(self.ratioMeanList))/mag.R2NomVal) - 1) * 10**6) - R2corr)
            self.stdR1ppm   = std(self.R1List, ddof=1) # in ppm
            self.C1R1       = mean(self.C1R1List)
            # self.C1R1       = float(((((self.R1/mean(ratioMeanC1))/mag.R2NomVal) - 1) * 10**6) - R2corr)
            self.C2R1       = mean(self.C2R1List)
            # self.C2R1       = float(((((self.R1/mean(ratioMeanC2))/mag.R2NomVal) - 1) * 10**6) - R2corr)
            self.stdC1R1    = std(self.C1R1List, ddof=1)
            self.stdC2R1    = std(self.C2R1List, ddof=1)
            self.stdMeanR1  = self.stdR1ppm/sqrt(len(self.R1List))
            self.meanR2     = mean(self.R2List) # this is mean of r1
            # self.meanR2     = float(((((self.R2*mean(self.ratioMeanList))/mag.R1NomVal) - 1) * 10**6) - R1corr)
            self.stdR2ppm   = std(self.R2List, ddof=1)
            self.C1R2       = mean(self.C1R2List)
            # self.C1R2       = float(((((self.R2*mean(ratioMeanC1))/mag.R1NomVal) - 1) * 10**6) - R1corr)
            self.C2R2       = mean(self.C2R2List)
            # self.C2R2       = float(((((self.R2*mean(ratioMeanC2))/mag.R1NomVal) - 1) * 10**6) - R1corr)
            self.stdC1R2    = std(self.C1R2List, ddof=1)
            self.stdC2R2    = std(self.C2R2List, ddof=1)
            self.stdMeanR2  = self.stdR2ppm/sqrt(len(self.R2List))
        else:
            self.ratioMean      = nan
            self.ratioStdMean   = nan
            self.meanR1         = nan
            self.meanR2         = nan
            self.stdR1ppm       = nan
            self.stdR2ppm       = nan
            self.C1R1           = nan
            self.C1R2           = nan
            self.C2R1           = nan
            self.C2R2           = nan
            self.stdC1R1        = nan
            self.stdC1R2        = nan
            self.stdC2R1        = nan
            self.stdC2R2        = nan
            self.stdMeanR1      = nan
            self.stdMeanR2      = nan

        if self.corr_bvdList != []:
            self.N         = len(self.corr_bvdList)
            self.bvd_mean  = mean(self.corr_bvdList)
            self.bvd_std   = std(self.corr_bvdList, ddof=1)
            self.bvd_stdMean   = self.bvd_std/sqrt(len(self.corr_bvdList))
        else:
            self.bvd_mean = nan
            self.bvd_std  = nan
            self.bvd_stdMean  = nan
        if self.bvdList_chk != []:
            self.bvd_mean_chk       = mean(self.bvdList_chk)
            self.bvd_std_chk        = std(self.bvdList_chk, ddof=1)
            self.bvd_stdmean_chk    = self.bvd_std_chk/sqrt(len(self.bvdList_chk))
        else:
            self.bvd_mean_chk       = nan
            self.bvd_std_chk        = nan
            self.bvd_stdmean_chk    = nan

        self.ratioMeanChkList = []
        self.R1MeanChkList    = []
        self.R2MeanChkList    = []
        if myDeltaI2R2 != 0 and self.bvdList_chk != []:
            for i, j in enumerate(self.bvdList_chk):
                self.ratioMeanChkList.append(compensation*(1 + (j/myDeltaI2R2)))
            self.ratioMeanChk   = mean(self.ratioMeanChkList) # calculated from bvd.txt file
            self.stdppm     = std(self.ratioMeanChkList, ddof=1)/mean(self.ratioMeanChkList)
            self.stdMeanPPM = self.stdppm/sqrt(len(self.ratioMeanChkList))
            # print (self.ratioMeanChkList)
        if mag.R2NomVal != 0 and mag.R1NomVal != 0:
            for i, j in enumerate(self.ratioMeanChkList):
                # print(j, self.R1, mag.R2NomVal, R2corr)
                self.R1MeanChkList.append((((self.R1/j) - mag.R2NomVal)/mag.R2NomVal) * 10**6 - R2corr) # this is actually R2
                self.R2MeanChkList.append(((self.R2*j - mag.R1NomVal)/mag.R1NomVal) * 10**6 - R1corr) # this is actually R1
            self.R1MeanChk    = mean(self.R1MeanChkList) # this is R2
            self.stdR1Chk     = std(self.R1MeanChkList, ddof=1) # this is R2
            self.stdMeanR1Chk = self.stdR1Chk/sqrt(len(self.R1MeanChkList)) # this is R2
            self.R2MeanChkOhm = (self.R1MeanChk/1000000 + 1) * mag.R2NomVal
            self.R2MeanChk    = mean(self.R2MeanChkList)
            self.stdR2Chk     = std(self.R2MeanChkList, ddof=1)
            self.stdMeanR2Chk = self.stdR2Chk/sqrt(len(self.R2MeanChkList))
            self.R1MeanChkOhm = (self.R2MeanChk/1000000 + 1) * mag.R1NomVal
        else:
            self.ratioMeanChk   = nan
            self.stdppm         = nan
            self.stdMeanPPM     = nan
            self.R1MeanChk      = nan
            self.stdR1Chk       = nan
            self.stdMeanR1Chk   = nan
            self.R2MeanChk      = nan
            self.stdR2Chk       = nan
            self.stdMeanR2Chk   = nan
            self.R1CorVal       = nan
            self.R2CorVal       = nan
            self.R1MeanChkOhm   = nan
            self.R2MeanChkOhm   = nan
            # self.remTime      = mag.measTime - (self.N*mag.fullCyc)
            # self.remTimeStamp = mag.sec2ts(self.remTime)
        self.R1CorVal = ((self.R1STPPred/1000000 + 1) * mag.R1NomVal)
        self.R2CorVal = ((self.R2STPPred/1000000 + 1) * mag.R2NomVal)
        # print('k: ', self.k)
        # print('Ratio Check: ', self.ratioMean,self.ratioMeanChk)
        # print('BVD Check: ', self.bvd_mean, self.bvd_mean_chk, ((self.bvd_mean - self.bvd_mean_chk)))
        # print('R Check: ', self.meanR1, self.R1MeanChk)

    def setValidData(self) -> None:
        """Sets the texts in all GUI line edits and spin boxes

        Returns
        -------
        None
        """
        global red_style
        global green_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.VMeanLineEdit.setText(str("{:.9e}".format(self.bvd_mean)))
        self.VMeanChkLineEdit.setText(str("{:.9e}".format(self.bvd_mean_chk)))
        self.Current1LineEdit.setText(str(self.dat.I1))
        self.FullCycLineEdit.setText(str(self.dat.fullCyc))
        if self.dat.calmode == True:
            self.lbl_calmode_rbv.setStyleSheet(green_style)
        else:
            self.lbl_calmode_rbv.setStyleSheet(red_style)
            self.user_warn_msg += "Compensation Calibration mode is OFF!\n"
        if self.dat.cnOutput == True:
            self.lbl_cnOutput_rbv.setStyleSheet(green_style)
        else:
            self.lbl_cnOutput_rbv.setStyleSheet(red_style)
            self.user_warn_msg += "Compensation is OFF!\n"
        if str(self.dat.low16) != '0':
            self.user_warn_msg += "16 Bit DAC is non-zero!\n"
        if self.SampUsedCt != 0:
            delay = ((int(self.IgnoredFirstLineEdit.text()) + int(self.IgnoredLastLineEdit.text()))/self.dat.SHC)*(self.dat.SHC*self.dat.intTime/self.dat.timeBase - self.dat.rampTime)
            meas = (self.dat.SHC*self.dat.intTime/self.dat.timeBase) - self.dat.rampTime - delay
            self.DelayLineEdit.setText(str("{:2.2f}".format(delay)))
            self.MeasLineEdit.setText(str("{:2.2f}".format(meas)))
        else:
            # self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))
            self.IgnoredFirstLineEdit.setText(str(self.dat.ignored_first))
            self.IgnoredLastLineEdit.setText(str(self.dat.ignored_last))
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
        self.CommentsTextBrowser.setText(self.dat.comments + ', Ratio: ' + str(self.ratioMean) + ' +/- ' + str(self.ratioStdMean))
        self.RelHumLineEdit.setText(str(self.dat.relHum))
        self.kLineEdit.setText(str("{:.12f}".format(self.k)))
        if self.k == 0:
            self.kLineEdit.setStyleSheet("color: red")
        else:
            self.kLineEdit.setStyleSheet("color: black")
        self.le_start_time.setText(str(self.dat.startDate))
        self.le_end_time.setText(str(self.dat.endDate))
        self.R1TempLineEdit.setText(str("{:.7f}".format(self.R1Temp)))
        self.R2TempLineEdit.setText(str("{:.7f}".format(self.R2Temp)))
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
        self.le_ratioStdMean.setText(str("{:.12f}".format(self.ratioStdMean)))
        self.StdDevLineEdit.setText(str("{:.6e}".format(self.bvd_std)))
        self.StdDevChkLineEdit.setText(str("{:.6e}".format(self.bvd_std_chk)))
        self.StdDevMeanLineEdit.setText(str("{:.6e}".format(self.bvd_stdMean)))
        self.StdDevMeanChkLineEdit.setText(str("{:.6e}".format(self.bvd_stdmean_chk)))
        # self.StdDevChkPPMLineEdit.setText(str("{:.7f}".format(self.stdppm*10**6)))
        self.NLineEdit.setText(str(self.N))
        self.MeasTimeLineEdit.setText(self.dat.measTimeStamp)
        self.le_range_shunt.setText('10k/' + str(self.dat.rangeShunt))
        # self.le_12bitdac.setText(str(int(self.k*2048*int(self.dat.rangeShunt)))+ '/' + str(self.dat.low16))
        self.le_12bitdac.setText(str(self.dat.dac12) + '/' + str(self.dat.low16)) # grab the values from config file
        # self.MDSSButton.setStyleSheet(red_style)
        self.MDSSButton.setEnabled(True)

        if not (self.deletePressed or self.restorePressed):
            self.plotCountCombo.clear()
            for i in range(len(self.corr_bvdList)):
                self.plotCountCombo.addItem(f'ct {len(self.corr_bvdList) - i - 1}')
        if self.deletePressed:
            self.deletePressed = False
        if self.restorePressed:
            self.restorePressed = False

        if len(self.corr_bvdList) > 625:
            self.bins = int(sqrt(len(self.corr_bvdList)))
        else:
            self.bins = 25
        self.stdR(self.RButStatus)
        self.SetResTab.update()

    def setInvalidData(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.validFile = False
        self.user_warn_msg = ""
        self.VMeanLineEdit.setText("")
        self.VMeanChkLineEdit.setText("")
        self.Current1LineEdit.setText("")
        self.FullCycLineEdit.setText("")
        self.MeasCycLineEdit.setText("")
        # self.SampUsedLineEdit.setText("")
        self.IgnoredFirstLineEdit.setText("")
        self.IgnoredLastLineEdit.setText("")
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
        self.le_start_time.setText("")
        self.le_end_time.setText("")
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
        self.le_ratioStdMean.setText("")
        self.StdDevLineEdit.setText("")
        self.StdDevMeanLineEdit.setText("")
        self.ppmMeanLineEdit.setText("")
        self.RMeanChkPPMLineEdit.setText("")
        self.StdDevPPMLineEdit.setText("")
        self.StdDevChkPPMLineEdit.setText("")
        self.StdDevPPM2LineEdit.setText("")
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
        self.le_range_shunt.setText("")
        self.le_12bitdac.setText("")
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
            self.StdDevPPM2LineEdit.setText(str("{:.7f}".format(self.stdR1ppm)))
            self.StdDevMeanPPMLineEdit.setText(str("{:.7f}".format(self.stdMeanR1)))
            self.StdDevChkPPMLineEdit.setText(str("{:.7f}".format(self.stdR1Chk)))
            err = (self.meanR1 - self.R1MeanChk)*1e3
            self.le_error.setText(str("{:.9f}".format(err)))
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
            self.StdDevPPM2LineEdit.setText(str("{:.7f}".format(self.stdR2ppm)))
            self.StdDevMeanPPMLineEdit.setText(str("{:.7f}".format(self.stdMeanR2)))
            self.StdDevChkPPMLineEdit.setText(str("{:.7f}".format(self.stdR2Chk)))
            err = (self.meanR2 - self.R2MeanChk)*1e3
            self.le_error.setText(str("{:.7f}".format(err)))
            if self.R2PPM:
                self.R2PPMLineEdit.setText(str("{:2.7f}".format(self.R2PPM)))
            else:
                self.R2PPMLineEdit.setText(str(0))

    def R1PresChanged(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                           ' Error: ' + str(e))
            self.R1PresLineEdit.setText(str("{:.4f}".format(self.R1Totpres)))
            pass

    def R2PresChanged(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                           ' Error: ' + str(e))
            self.R2PresLineEdit.setText(str("{:.4f}".format(self.R2Totpres)))
            pass

    def oilDepth1Changed(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.R1OilDepth = self.R1OilDepthSpinBox.value()
        self.updateOilDepth('R1')
        if self.bvd_stat_obj is not None:
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)

    def oilDepth2Changed(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.R2OilDepth = self.R2OilDepthSpinBox.value()
        self.updateOilDepth('R2')
        if self.bvd_stat_obj is not None:
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)

    def updateOilDepth(self, R: str) -> None:
        global g
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        try:
            self.R1Temp = float(self.R1TempLineEdit.text())
            if self.bvd_stat_obj is not None:
                self.cleanUp()
                self.getBVD()
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
        except Exception as e:
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                           ' Error: ' + str(e))
            self.R1TempLineEdit.setText(str("{:.4f}".format(self.R1Temp)))
            pass

    def temp2Changed(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        try:
            self.R2Temp = float(self.R2TempLineEdit.text())
            if self.bvd_stat_obj is not None:
                self.cleanUp()
                self.getBVD()
                self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
                self.setValidData()
                self.plotBVD()
        except Exception as e:
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                           ' Error: ' + str(e))
            self.R2TempLineEdit.setText(str("{:.4f}".format(self.R2Temp)))
            pass

    def folderClicked(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.dialog.exec():
            self.txtFilePath = self.dialog.selectedFiles()[0]
            # print('Loading datafile: ', self.txtFilePath)
            self.txtFileLineEdit.setText(self.txtFilePath)
            self.validFile = False
            self.chb_outlier.setCheckState(Qt.CheckState.Unchecked)
            self.outliers=False
            self.draw_flag = False
            self.user_warn_msg = ""
            self.getData()
        else:
            self.txtFilePath = ''

    def get_temperature1(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.temperature1_folder = self.temperature1_dialog.getExistingDirectory(None, "Select Folder")
        self.le_path_temperature1.setText(self.temperature1_folder)

    def get_temperature2(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.temperature2_folder = self.temperature2_dialog.getExistingDirectory(None, "Select Folder")
        self.le_path_temperature2.setText(self.temperature2_folder)

    def folderEdited(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.txtFilePath = self.txtFileLineEdit.text()
        self.validFile = False
        self.getData()

    def temperature1_folder_edited(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.temperature1_folder = self.le_path_temperature1.text()

    def temperature2_folder_edited(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.temperature2_folder = self.le_path_temperature2.text()

    def MDSSClicked(self) -> None:
        global red_style
        global green_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
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
            # self.progressBar.setProperty('value', 0)

    def saveMDSS(self) -> None:
        global red_style
        self.mdssdir = ""
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if site == 'NIST':
            self.mdssdir = "C:" + os.sep + "Users" + os.sep + os.getlogin() + os.sep + "Desktop" + os.sep + r"Transfer Files"
            if not os.path.isdir(self.mdssdir):
                os.mkdir(self.mdssdir)
        else:
            tempdir = self.txtFilePath.split('/')
            tempdir.pop(-1)
            for i in tempdir:
                self.mdssdir = self.mdssdir + i + os.sep
        # self.progressBar.setProperty('value', 25)

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
                      N=self.N, samplesUsed= int(self.dat.SHC) - (int(self.IgnoredFirstLineEdit.text()) + int(self.IgnoredLastLineEdit.text())), \
                      meas=float(self.MeasLineEdit.text()), delay=float(self.DelayLineEdit.text()), \
                      R1PredictionSTP=float(self.R1STPLineEdit.text()), R2PredictionSTP=float(self.R2STPLineEdit.text()), \
                      comments = str(self.dat.comments))
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
                           '# Meas/Stats: ' + str(self.SHCLineEdit.text() + '/' + str(int(self.dat.SHC) - (int(self.IgnoredFirstLineEdit.text()) + int(self.IgnoredLastLineEdit.text())))) + '\n' + '# Full Cycle Time: ' + str(self.FullCycLineEdit.text()) + '\n' + \
                           '# Ramp Time: ' + str(self.RampLineEdit.text()) + '\n' + '# Measurement Time: ' + str(self.MeasLineEdit.text()) + '\n' + \
                           '# Delay: ' + str(self.DelayLineEdit.text()) + '\n' + \
                           '# Comment: ' + str(self.CommentsTextBrowser.toPlainText()) + '\n' + \
                           '# BVD [V]' + '\t' + 'Ratio' + '\t' + 'StdrtN[BVD]' + '\t' + 'StdrtN[Ratio]' + '\n\n')

        with open(self.pathString + '_pyBV.mea', 'w') as mea_file:
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
                            '# Meas/Stats: ' + str(self.SHCLineEdit.text() + '/' + str(int(self.dat.SHC) - (int(self.IgnoredFirstLineEdit.text()) + int(self.IgnoredLastLineEdit.text())))) + '\n' + '# Full Cycle Time: ' + str(self.FullCycLineEdit.text()) + '\n' + \
                            '# Ramp Time: ' + str(self.RampLineEdit.text()) + '\n' + '# Measurement Time: ' + str(self.MeasLineEdit.text()) + '\n' + \
                            '# Delay: ' + str(self.DelayLineEdit.text()) + '\n' + \
                            '# Comment: ' + str(self.CommentsTextBrowser.toPlainText()) + '\n' + \
                            '# V(I-) [V]' + '\t' + 'V(I+) [V]' + '\n\n')

        with open(self.pathString + '_pyCCCRAW.mea', 'a') as mea_file:
            for i, j, k, l in zip(self.corr_bvdList, self.ratioMeanList, self.stdbvdList, self.ratioMeanStdList):
                mea_file.write(str(i) + '\t' + str(j) + '\t' + str(k) + '\t' + str(l) + '\n')

        with open(self.pathString + '_pyBV.mea', 'a') as mea_file:
            for i, j in zip(self.AA, self.BB):
                mea_file.write(str(i) + '\t' + str(j) + '\n')

        self.saveStatus = False
        self.MDSSButton.setStyleSheet(red_style)
        self.MDSSButton.setText('No')
        self.saveButton.setEnabled(False)
        self.statusbar.showMessage('Saved to ' + str(self.mdssdir), 5000)

    def cleanUp(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.deletedV1      = []
        self.deletedV2      = []
        self.deletedCount   = []
        self.deletedBVD     = []
        self.deletedBVDChk  = []

        self.bvdList        = []
        self.corr_bvdList   = []
        self.stdbvdList     = []
        self.bvdCount       = []
        self.deletedR1      = []
        self.deletedR2      = []

        self.bvdList_chk        = []

        self.SampUsedCt     = 0
        self.changedDeltaI2R2Ct = 0
        self.changedR1STPBool = False
        self.changedR2STPBool = False
        self.CommentsTextBrowser.setText("")

    def deleteBut(self) -> None:
        self.deletePressed = True
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.plottedBVD and self.plotCountCombo.count():
            curIndex = self.plotCountCombo.count() - self.plotCountCombo.currentIndex() - 1
            # print("Current Index:", curIndex)

            self.deletedIndex.append(curIndex)
            self.deletedCount.append(int(self.plotCountCombo.currentText().replace('ct ', '')))
            if int(curIndex) >= 0:
                self.plotCountCombo.removeItem(int(self.plotCountCombo.count() - curIndex - 1))
            self.deletedBVD.append(self.corr_bvdList[curIndex])
            self.deletedBVDChk.append(self.bvdList_chk[curIndex])
            self.deletedV1.append(self.V1[curIndex])
            self.deletedV2.append(self.V2[curIndex])
            self.deletedR1.append(self.R1List[curIndex])
            self.deletedR2.append(self.R2List[curIndex])
            self.V1.pop(curIndex)
            self.V2.pop(curIndex)
            self.corr_bvdList.pop(curIndex)
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
        self.restorePressed = True
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.deletedCount != []:
            print(self.deletedIndex)
            self.plotCountCombo.insertItem(int(self.N - self.deletedIndex[-1]), f'ct {int(self.deletedIndex[-1])}')
            self.V1.insert(self.deletedIndex[-1], self.deletedV1[-1])
            self.V2.insert(self.deletedIndex[-1], self.deletedV2[-1])
            self.bvdCount.insert(self.deletedIndex[-1], self.deletedCount[-1])
            self.corr_bvdList.insert(self.deletedIndex[-1], self.deletedBVD[-1])
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
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.getData()
        # self.cleanUp()
        # self.getBVD()
        # self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
        # self.setValidData()
        # self.plotBVD()
        # self.plotStatMeasures()

def dir_path(save_path):
    """
    """
    save_path = str(save_path)
    if not os.path.isdir(save_path):
        os.mkdir(save_path)
    return save_path

if __name__ == "__main__":
    parser = ArgumentParser(prog = 'Magnicon-Offline-Analyzer',
                            description='Configure Magnicon-Offline-Analyzer',
                            epilog='A utility to interact with the analysis software for Magnicon CCC systems', add_help=True)
    parser.add_argument('-db', '--db_path', help='Specify resistor database directory', default="", type=str)
    parser.add_argument('-l', '--log_path', help='Specify log directory', default="C:" + os.sep + "_logcache_", type=dir_path)
    parser.add_argument('-d', '--debug', help='Debugging mode', action='store_true')
    parser.add_argument('-s', '--site', help='Site where this program is used', default="", type=str)
    parser.add_argument('-c', '--specific_gravity', help='Specific gravity of oil for oil type resistors', default=0.8465, type=float)
    args, unk = parser.parse_known_args()
    if unk:
        logger.debug("Warning: Ignoring unknown arguments: {:}".format(unk))
        pass
    dbdir = args.db_path
    logdir = args.log_path
    debug_mode = args.debug
    site = args.site
    c = args.specific_gravity
    # define the file handler and formatting
    lfname = logdir + os.sep + 'debug_magnicon-offline-analyzer' + '.log'
    file_handler = TimedRotatingFileHandler(lfname, when='midnight')
    fmt = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    # Handle high resolution displays:
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("windowsvista")
    mainWindow = QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec())