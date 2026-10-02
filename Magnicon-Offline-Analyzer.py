# -*- coding: utf-8 -*-
"""
Created on Tue Jun 24 11:08:20 2025

@author: ohm
"""

import sys, os
from time import perf_counter
import inspect
import traceback
import csv
from datetime import datetime

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import Qt, QRect, QMetaObject, QCoreApplication, QLocale
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainterPath, QPainter,\
                        QKeySequence, QDoubleValidator
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, \
                             QLabel, QPushButton, QComboBox, QTextBrowser, QTabWidget, \
                             QSpacerItem, QGridLayout, QLineEdit, QFrame, QSizePolicy, \
                             QMenuBar, QSpinBox, QToolButton, QStatusBar, \
                             QTextEdit, QFileDialog, QCheckBox, QMessageBox, QProgressDialog)

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, ScalarFormatter, MultipleLocator, NullLocator
import matplotlib.style as mplstyle
from numpy import sqrt, std, mean, ones, linspace, array, nan, polyfit
from scipy import signal
import allantools

# custom imports
from bvd_stats import bvd_stat
from magnicon_ccc import magnicon_ccc
from create_mag_ccc_datafile import writeDataFile
import mystat
from env import env
from ccc_diagram import draw_ccc_diagram
from ResDataBase import MYSQL_DEFAULTS
from argparse import ArgumentParser

import logging
from logging.handlers import TimedRotatingFileHandler

# base directory of the project
base_dir = os.path.dirname(os.path.abspath(__file__))
# Create the logger
logger = logging.getLogger(__name__)
# set the log level
logger.setLevel(logging.DEBUG)

# python globals
__version__             = '3.2.0' # Program version string
red_style               = "color: white; background-color: red; border: 0.5px solid black"
blue_style              = "color: white; background-color: blue; border: 0.5px solid black"
green_style             = "color: white; background-color: green; border:0.5px solid black"
le_style                = """QLineEdit { border: 0.5px solid black; background-color: rgb(255, 255, 255); color: black }"""
le_readonly_style       = """QLineEdit { border: 0.5px solid black; background-color: rgb(215, 214, 213); color: black }"""
le_readonly_bold_style  = """QLineEdit { border: 0.5px solid black; background-color: rgb(215, 214, 213); color: black; font-weight: bold }"""
# columns of the batch summary csv file
batch_csv_fields = ['File', 'Status', 'Start Time', 'End Time', 'Standard', 'R1 Serial', 'R2 Serial', \
                    'Mean [uOhm/Ohm]', 'Std. Dev. [uOhm/Ohm]', 'Std. Mean [uOhm/Ohm]', 'R Mean Chk [uOhm/Ohm]', \
                    'R Mean - Chk [ppb]', 'C1-C2 [uOhm/Ohm]', 'Ratio Mean', 'Ratio Std. Mean', 'BVD Mean [V]', \
                    'BVD Std. Mean [V]', 'N', 'Ignored First', 'Ignored Last', 'R1 Temperature [C]', \
                    'R2 Temperature [C]', 'R1 Total Pres. [Pa]', 'R2 Total Pres. [Pa]', 'R1STPPred [uOhm/Ohm]', \
                    'R2STPPred [uOhm/Ohm]', 'Remove Outliers', 'Quad Corr', 'Process', 'pymdss File', 'Warnings', 'Error']
mysql_config = None # MySQL resistor database settings from the command line, None: ResDataBase.MYSQL_DEFAULTS
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

def float_validator() -> QDoubleValidator:
    """Validator for numeric line edits that only accepts text python's float() can parse,
       i.e. '.' as the decimal point and no group separators like '101,325'
    """
    validator = QDoubleValidator()
    locale = QLocale(QLocale.Language.C)
    locale.setNumberOptions(QLocale.NumberOption.OmitGroupSeparator | QLocale.NumberOption.RejectGroupSeparator)
    validator.setLocale(locale)
    return validator

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
        mainWindow.closeEvent = self.closeEvent
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

        self.batch_action = QAction("&Batch Process...")
        self.batch_action.setStatusTip("Process and save several data files with the current settings")
        self.batch_action.triggered.connect(self.batchProcess)
        self.batch_action.setShortcut(QKeySequence("Ctrl+b"))
        self.batch_action.setShortcutVisibleInContextMenu(True)

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
        if index == 0 and self.validFile and not self.draw_flag:
            self.updateCCCDiagram()

    def updateCCCDiagram(self) -> None:
        """Draws the CCC diagram with the values of the loaded file"""
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.CCCDiagram(round(self.dat.R1NomVal, 2), round(self.dat.R2NomVal, 2), self.dat.N1, self.dat.N2, \
                        format(self.dat.I1, ".1e"), format(self.dat.I2, ".1e"), format(self.dat.bvdMean, ".1e"), \
                        self.dat.NA, "10k*" + str(self.dat.dac12), "10k/" + str(self.dat.rangeShunt), format(self.dat.I1*self.k, ".1e"))
        self.draw_flag = True

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
        self.file_menu.addAction(self.batch_action)
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

    def closeEvent(self, event) -> None:
        """Closing the main window quits the program, also closing the About and Timing Diagram windows"""
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        event.accept()
        QApplication.quit()

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
        app.quit()

    def initializations(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        global g
        self.txtFilePath  = ''
        # flags
        self.validFile    = False
        self.outliers     = False
        self.qhrCharFlag  = False
        self.plottedBVD   = False
        self.plottedRaw   = False
        self.plottedAllan = False
        self.plottedSpec  = False
        self.SampUsedCt = 0
        self.changedDeltaI2R2Ct = 0
        self.changedR1STPBool = False
        self.changedR2STPBool = False
        self.draw_flag = False
        self.user_warn_msg = ""
        self.outlierPressed = False
        self.detrend_state = 0
        self.batchMode = False # True while batch processing: no plots, ADEV/PSD or warning dialogs

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

        self.bvdCount           = [] # cycle numbers of the cycles used in the results
        self.bvdfitList         = []
        self.deletedCycles      = [] # cycles deleted by the user, in the order they were deleted
        self.outlierCycles      = set() # cycles left out by Remove Outliers
        self.dat                = None # magnicon_ccc class object
        self.bvd_stat_obj       = None # bvd_stats class object
        # per-cycle lists for all the cycles, selectCycles() makes the lists used in the results from these
        self.bvdList            = []
        self.V1_all             = []
        self.V2_all             = []
        self.stdbvdList_all     = []
        self.bvdList_chk_all    = []
        self.bvdList_overlap_all = [] # BVD with overlapping quadratic drift removal (Quad Corr: Overlap)
        # per-cycle lists without the outlier and deleted cycles
        self.corr_bvdList       = []
        self.stdbvdList         = []
        self.bvdList_chk        = []
        self.bvdList_overlap    = []
        self.V1                 = []
        self.V2                 = []
        self.A                  = []
        self.B                  = []
        self.stdA               = []
        self.stdB               = []

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
        self.lbl_Bfield = QLabel(parent=self.SetResTab)
        self.lbl_Bfield.setGeometry(QRect(self.col4x, 700, self.lbl_width - 25, self.lbl_height))
        self.lbl_Bfield.setHidden(True)
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
        self.lbl_sampleTemp = QLabel(parent=self.SetResTab)
        self.lbl_sampleTemp.setGeometry(QRect(self.col4x+46, 700, self.lbl_width - 25, self.lbl_height))
        self.lbl_sampleTemp.setHidden(True)
        self.lbl_contact = QLabel(parent=self.SetResTab)
        self.lbl_contact.setGeometry(QRect(self.col4x+114, 700, self.lbl_width - 25, self.lbl_height))
        self.lbl_contact.setHidden(True)
        self.lbl_qhr_system = QLabel(parent=self.SetResTab)
        self.lbl_qhr_system.setGeometry(QRect(self.col4x+195, 700, self.lbl_width - 25, self.lbl_height))
        self.lbl_qhr_system.setHidden(True)
        self.lbl_carrier_density = QLabel(parent=self.SetResTab)
        self.lbl_carrier_density.setGeometry(QRect(self.col4x+290, 700, self.lbl_width - 25, self.lbl_height))
        self.lbl_carrier_density.setHidden(True)
        # col7
        self.StandardRLabel = QLabel(parent=self.centralwidget)
        self.StandardRLabel.setGeometry(QRect(self.col7x, 30, self.lbl_width, self.lbl_height))
        self.MDSSLabel = QLabel(parent=self.centralwidget)
        self.MDSSLabel.setGeometry(QRect(self.col7x, 90, self.lbl_width, self.lbl_height))
        self.ppmMeanLabel = QLabel(parent=self.centralwidget)
        self.ppmMeanLabel.setGeometry(QRect(self.col7x, 210, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLabel = QLabel(parent=self.centralwidget)
        self.RMeanChkPPMLabel.setGeometry(QRect(self.col7x, 265, self.lbl_width, self.lbl_height))
        self.StdDevPPM2Label = QLabel(parent=self.centralwidget)
        self.StdDevPPM2Label.setGeometry(QRect(self.col7x, 320, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLabel = QLabel(parent=self.centralwidget)
        self.StdDevMeanPPMLabel.setGeometry(QRect(self.col7x, 375, self.lbl_width, self.lbl_height))
        self.C1C2Label = QLabel(parent=self.centralwidget)
        self.C1C2Label.setGeometry(QRect(self.col7x, 430, self.lbl_width, self.lbl_height))
        self.RatioMeanLabel = QLabel(parent=self.centralwidget)
        self.RatioMeanLabel.setGeometry(QRect(self.col7x, 485, self.lbl_width, self.lbl_height))
        self.lbl_ratioStdMean = QLabel(parent=self.centralwidget)
        self.lbl_ratioStdMean.setGeometry(QRect(self.col7x, 540, self.lbl_width, self.lbl_height))
        self.IgnoredFirstLabel = QLabel(parent=self.centralwidget)
        self.IgnoredFirstLabel.setGeometry(QRect(self.col7x, 595, self.lbl_width, self.lbl_height))
        self.IgnoredLastLabel = QLabel(parent=self.centralwidget)
        self.IgnoredLastLabel.setGeometry(QRect(self.col7x, 650, self.lbl_width, self.lbl_height))
        self.lbl_error = QLabel(parent=self.centralwidget)
        self.lbl_error.setGeometry(QRect(self.col7x, 705, self.lbl_width, self.lbl_height))
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
        self.R1SNLineEdit.setStyleSheet(le_readonly_style)
        self.R2SNLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2SNLineEdit.setGeometry(QRect(self.col0x, self.coly*2 , self.lbl_width, self.lbl_height))
        self.R2SNLineEdit.setReadOnly(True)
        self.R2SNLineEdit.setStyleSheet(le_readonly_style)
        self.AppVoltLineEdit = QLineEdit(parent=self.SetResTab)
        self.AppVoltLineEdit.setGeometry(QRect(self.col0x, self.coly*3, self.lbl_width, self.lbl_height))
        self.AppVoltLineEdit.setReadOnly(True)
        self.AppVoltLineEdit.setStyleSheet(le_readonly_style)
        self.N1LineEdit = QLineEdit(parent=self.SetResTab)
        self.N1LineEdit.setGeometry(QRect(self.col0x, self.coly*4, self.lbl_width, self.lbl_height))
        self.N1LineEdit.setReadOnly(True)
        self.N1LineEdit.setStyleSheet(le_readonly_style)
        self.MeasCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasCycLineEdit.setGeometry(QRect(self.col0x, self.coly*5, self.lbl_width, self.lbl_height))
        self.MeasCycLineEdit.setReadOnly(True)
        self.MeasCycLineEdit.setStyleSheet(le_readonly_style)
        self.FullCycLineEdit = QLineEdit(parent=self.SetResTab)
        self.FullCycLineEdit.setGeometry(QRect(self.col0x, self.coly*6, self.lbl_width, self.lbl_height))
        self.FullCycLineEdit.setReadOnly(True)
        self.FullCycLineEdit.setStyleSheet(le_readonly_style)
        self.R1PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1PresLineEdit.setGeometry(QRect(self.col0x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1PresLineEdit.setValidator(float_validator())
        self.R1PresLineEdit.setStyleSheet(le_style)
        self.R1PresLineEdit.returnPressed.connect(self.R1PresChanged)
        self.R2PresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PresLineEdit.setGeometry(QRect(self.col0x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2PresLineEdit.setValidator(float_validator())
        self.R2PresLineEdit.setStyleSheet(le_style)
        self.R2PresLineEdit.returnPressed.connect(self.R2PresChanged)
        self.txtFileLineEdit = QLineEdit(parent=self.SetResTab)
        self.txtFileLineEdit.setGeometry(QRect(self.col0x, self.coly*10 + 30, int(self.lbl_width*2.8), self.lbl_height))
        self.txtFileLineEdit.returnPressed.connect(self.folderEdited)
        # col1
        self.R1PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1PPMLineEdit.setGeometry(QRect(self.col1x, self.coly, self.lbl_width, self.lbl_height))
        self.R1PPMLineEdit.setReadOnly(True)
        self.R1PPMLineEdit.setStyleSheet(le_readonly_style)
        self.R2PPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2PPMLineEdit.setGeometry(QRect(self.col1x, self.coly*2, self.lbl_width, self.lbl_height))
        self.R2PPMLineEdit.setReadOnly(True)
        self.R2PPMLineEdit.setStyleSheet(le_readonly_style)
        self.Current1LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current1LineEdit.setGeometry(QRect(self.col1x, self.coly*3, self.lbl_width, self.lbl_height))
        self.Current1LineEdit.setReadOnly(True)
        self.Current1LineEdit.setStyleSheet(le_readonly_style)
        self.N2LineEdit = QLineEdit(parent=self.SetResTab)
        self.N2LineEdit.setGeometry(QRect(self.col1x, self.coly*4, self.lbl_width, self.lbl_height))
        self.N2LineEdit.setReadOnly(True)
        self.N2LineEdit.setStyleSheet(le_readonly_style)
        self.SHCLineEdit = QLineEdit(parent=self.SetResTab)
        self.SHCLineEdit.setGeometry(QRect(self.col1x, self.coly*5, self.lbl_width, self.lbl_height))
        self.SHCLineEdit.setReadOnly(True)
        self.SHCLineEdit.setStyleSheet(le_readonly_style)
        self.RampLineEdit = QLineEdit(parent=self.SetResTab)
        self.RampLineEdit.setGeometry(QRect(self.col1x, self.coly*6, self.lbl_width, self.lbl_height))
        self.RampLineEdit.setReadOnly(True)
        self.RampLineEdit.setStyleSheet(le_readonly_style)
        self.le_path_temperature1 = QLineEdit(parent=self.SetResTab)
        self.le_path_temperature1.setGeometry(QRect(self.col1x, self.coly*11 + 30, self.lbl_width+80, self.lbl_height))
        self.le_path_temperature1.setStyleSheet(le_style)

        self.le_path_temperature2 = QLineEdit(parent=self.SetResTab)
        self.le_path_temperature2.setGeometry(QRect(self.col1x, self.coly*12 + 30, self.lbl_width+80, self.lbl_height))
        self.le_path_temperature2.setStyleSheet(le_style)

        self.le_range_shunt = QLineEdit(parent=self.SetResTab)
        self.le_range_shunt.setGeometry(QRect(self.col1x-40, self.coly*8+40, self.lbl_width-60, self.lbl_height))
        self.le_range_shunt.setReadOnly(True)
        self.le_range_shunt.setStyleSheet(le_readonly_style)
        # col2
        self.R1ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1ValueLineEdit.setGeometry(QRect(self.col2x, self.coly, self.lbl_width, self.lbl_height))
        self.R1ValueLineEdit.setReadOnly(True)
        self.R1ValueLineEdit.setStyleSheet(le_readonly_style)
        self.R2ValueLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2ValueLineEdit.setGeometry(QRect(self.col2x, self.coly*2, self.lbl_width, self.lbl_height))
        self.R2ValueLineEdit.setReadOnly(True)
        self.R2ValueLineEdit.setStyleSheet(le_readonly_style)
        self.Current2LineEdit = QLineEdit(parent=self.SetResTab)
        self.Current2LineEdit.setGeometry(QRect(self.col2x, self.coly*3, self.lbl_width, self.lbl_height))
        self.Current2LineEdit.setReadOnly(True)
        self.Current2LineEdit.setStyleSheet(le_readonly_style)
        self.NAuxLineEdit = QLineEdit(parent=self.SetResTab)
        self.NAuxLineEdit.setGeometry(QRect(self.col2x, self.coly*4, self.lbl_width, self.lbl_height))
        self.NAuxLineEdit.setReadOnly(True)
        self.NAuxLineEdit.setStyleSheet(le_readonly_style)
        self.DelayLineEdit = QLineEdit(parent=self.SetResTab)
        self.DelayLineEdit.setGeometry(QRect(self.col2x, self.coly*5, self.lbl_width, self.lbl_height))
        self.DelayLineEdit.setReadOnly(True)
        self.DelayLineEdit.setStyleSheet(le_readonly_style)
        self.MeasLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasLineEdit.setGeometry(QRect(self.col2x, self.coly*6, self.lbl_width, self.lbl_height))
        self.MeasLineEdit.setReadOnly(True)
        self.MeasLineEdit.setStyleSheet(le_readonly_style)
        self.R1OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1OilPresLineEdit.setGeometry(QRect(self.col2x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R1OilPresLineEdit.setReadOnly(True)
        self.R1OilPresLineEdit.setStyleSheet(le_readonly_style)
        self.R2OilPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2OilPresLineEdit.setGeometry(QRect(self.col2x, self.coly*8, self.lbl_width, self.lbl_height))
        self.R2OilPresLineEdit.setReadOnly(True)
        self.R2OilPresLineEdit.setStyleSheet(le_readonly_style)
        # col3
        self.kLineEdit = QLineEdit(parent=self.SetResTab)
        self.kLineEdit.setGeometry(QRect(self.col3x, self.coly, self.lbl_width, self.lbl_height))
        self.kLineEdit.setReadOnly(True)
        self.kLineEdit.setStyleSheet(le_readonly_style)
        self.MeasTimeLineEdit = QLineEdit(parent=self.SetResTab)
        self.MeasTimeLineEdit.setGeometry(QRect(self.col3x, self.coly*2, self.lbl_width, self.lbl_height))
        self.MeasTimeLineEdit.setReadOnly(True)
        self.MeasTimeLineEdit.setStyleSheet(le_readonly_style)
        self.le_deltaI2R2 = QLineEdit(parent=self.SetResTab)
        self.le_deltaI2R2.setGeometry(QRect(self.col3x, self.coly*3, self.lbl_width, self.lbl_height))
        self.le_deltaI2R2.setStyleSheet(le_style)
        self.le_deltaI2R2.returnPressed.connect(self.changedDeltaI2R2)
        self.R1TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TotalPresLineEdit.setGeometry(QRect(self.col3x, self.coly*4, self.lbl_width, self.lbl_height))
        self.R1TotalPresLineEdit.setReadOnly(True)
        self.R1TotalPresLineEdit.setStyleSheet(le_readonly_style)
        self.R2TotalPresLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TotalPresLineEdit.setGeometry(QRect(self.col3x, self.coly*5, self.lbl_width, self.lbl_height))
        self.R2TotalPresLineEdit.setReadOnly(True)
        self.R2TotalPresLineEdit.setStyleSheet(le_readonly_style)
        self.R1TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1TempLineEdit.setGeometry(QRect(self.col3x, self.coly*6, self.lbl_width, self.lbl_height))
        self.R1TempLineEdit.setValidator(float_validator())
        self.R1TempLineEdit.setStyleSheet(le_style)
        self.R1TempLineEdit.returnPressed.connect(self.temp1Changed)
        self.R2TempLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2TempLineEdit.setGeometry(QRect(self.col3x, self.coly*7, self.lbl_width, self.lbl_height))
        self.R2TempLineEdit.setValidator(float_validator())
        self.R2TempLineEdit.setStyleSheet(le_style)
        self.R2TempLineEdit.returnPressed.connect(self.temp2Changed)
        self.RelHumLineEdit = QLineEdit(parent=self.SetResTab)
        self.RelHumLineEdit.setGeometry(QRect(self.col3x, self.coly*8, self.lbl_width, self.lbl_height))
        self.RelHumLineEdit.setReadOnly(True)
        self.RelHumLineEdit.setStyleSheet(le_readonly_style)
        self.le_start_time = QLineEdit(parent=self.SetResTab)
        self.le_start_time.setGeometry(QRect(self.col3x, self.coly*9 + 30, self.lbl_width, self.lbl_height))
        self.le_start_time.setReadOnly(True)
        self.le_start_time.setStyleSheet(le_readonly_style)
        self.le_end_time = QLineEdit(parent=self.SetResTab)
        self.le_end_time.setGeometry(QRect(self.col3x, self.coly*10 + 30, self.lbl_width, self.lbl_height))
        self.le_end_time.setReadOnly(True)
        self.le_end_time.setStyleSheet(le_readonly_style)
        self.le_12bitdac = QLineEdit(parent=self.SetResTab)
        self.le_12bitdac.setGeometry(QRect(self.col3x - 100, self.coly*8 + 40, self.lbl_width-20, self.lbl_height))
        self.le_12bitdac.setReadOnly(True)
        self.le_12bitdac.setStyleSheet(le_readonly_style)
        # col4
        self.VMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanLineEdit.setGeometry(QRect(self.col4x, self.coly, self.lbl_width, self.lbl_height))
        self.VMeanLineEdit.setReadOnly(True)
        self.VMeanLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevLineEdit.setGeometry(QRect(self.col4x, self.coly*2, self.lbl_width, self.lbl_height))
        self.StdDevLineEdit.setReadOnly(True)
        self.StdDevLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevMeanLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanLineEdit.setGeometry(QRect(self.col4x, self.coly*3, self.lbl_width, self.lbl_height))
        self.StdDevMeanLineEdit.setReadOnly(True)
        self.StdDevMeanLineEdit.setStyleSheet(le_readonly_style)
        self.C1LineEdit = QLineEdit(parent=self.SetResTab)
        self.C1LineEdit.setGeometry(QRect(self.col4x, self.coly*4, self.lbl_width, self.lbl_height))
        self.C1LineEdit.setStyleSheet("")
        self.C1LineEdit.setReadOnly(True)
        self.C1LineEdit.setStyleSheet(le_readonly_style)
        self.C2LineEdit = QLineEdit(parent=self.SetResTab)
        self.C2LineEdit.setGeometry(QRect(self.col4x, self.coly*5, self.lbl_width, self.lbl_height))
        self.C2LineEdit.setStyleSheet("")
        self.C2LineEdit.setReadOnly(True)
        self.C2LineEdit.setStyleSheet(le_readonly_style)
        # col5
        self.VMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.VMeanChkLineEdit.setGeometry(QRect(self.col5x, self.coly, self.lbl_width, self.lbl_height))
        self.VMeanChkLineEdit.setReadOnly(True)
        self.VMeanChkLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkLineEdit.setGeometry(QRect(self.col5x, self.coly*2, self.lbl_width, self.lbl_height))
        self.StdDevChkLineEdit.setReadOnly(True)
        self.StdDevChkLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevMeanChkLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevMeanChkLineEdit.setGeometry(QRect(self.col5x, self.coly*3, self.lbl_width, self.lbl_height))
        self.StdDevMeanChkLineEdit.setReadOnly(True)
        self.StdDevMeanChkLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevC1LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC1LineEdit.setGeometry(QRect(self.col5x, self.coly*4, self.lbl_width, self.lbl_height))
        self.StdDevC1LineEdit.setReadOnly(True)
        self.StdDevC1LineEdit.setStyleSheet(le_readonly_style)
        self.StdDevC2LineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevC2LineEdit.setGeometry(QRect(self.col5x, self.coly*5, self.lbl_width, self.lbl_height))
        self.StdDevC2LineEdit.setReadOnly(True)
        self.StdDevC2LineEdit.setStyleSheet(le_readonly_style)
        # col6
        self.R1STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R1STPLineEdit.setGeometry(QRect(self.col6x, self.coly, self.lbl_width - 5, self.lbl_height))
        self.R1STPLineEdit.setReadOnly(False)
        self.R1STPLineEdit.setValidator(float_validator())
        self.R1STPLineEdit.returnPressed.connect(self.changedR1STPPred)
        self.R1STPLineEdit.setStyleSheet(le_style)
        self.R2STPLineEdit = QLineEdit(parent=self.SetResTab)
        self.R2STPLineEdit.setGeometry(QRect(self.col6x, self.coly*2, self.lbl_width - 5, self.lbl_height))
        self.R2STPLineEdit.setReadOnly(False)
        self.R2STPLineEdit.setValidator(float_validator())
        self.R2STPLineEdit.returnPressed.connect(self.changedR2STPPred)
        self.R2STPLineEdit.setStyleSheet(le_style)
        self.NLineEdit = QLineEdit(parent=self.SetResTab)
        self.NLineEdit.setGeometry(QRect(self.col6x, self.coly*3, self.lbl_width- 5, self.lbl_height))
        self.NLineEdit.setReadOnly(True)
        self.NLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevPPMLineEdit.setGeometry(QRect(self.col6x, self.coly*4, self.lbl_width - 5, self.lbl_height))
        self.StdDevPPMLineEdit.setReadOnly(True)
        self.StdDevPPMLineEdit.setStyleSheet(le_readonly_style)
        self.StdDevChkPPMLineEdit = QLineEdit(parent=self.SetResTab)
        self.StdDevChkPPMLineEdit.setGeometry(QRect(self.col6x, self.coly*5, self.lbl_width - 5, self.lbl_height))
        self.StdDevChkPPMLineEdit.setReadOnly(True)
        self.StdDevChkPPMLineEdit.setStyleSheet(le_readonly_style)
        # col7
        self.ppmMeanLineEdit = QLineEdit(parent=self.centralwidget)
        self.ppmMeanLineEdit.setGeometry(QRect(self.col7x, 237, self.lbl_width, self.lbl_height))
        self.ppmMeanLineEdit.setReadOnly(True)
        self.ppmMeanLineEdit.setStyleSheet(le_readonly_bold_style)
        self.RMeanChkPPMLineEdit = QLineEdit(parent=self.centralwidget)
        self.RMeanChkPPMLineEdit.setGeometry(QRect(self.col7x, 292, self.lbl_width, self.lbl_height))
        self.RMeanChkPPMLineEdit.setReadOnly(True)
        self.RMeanChkPPMLineEdit.setStyleSheet(le_readonly_bold_style)
        self.StdDevPPM2LineEdit = QLineEdit(parent=self.centralwidget)
        self.StdDevPPM2LineEdit.setGeometry(QRect(self.col7x, 347, self.lbl_width, self.lbl_height))
        self.StdDevPPM2LineEdit.setReadOnly(True)
        self.StdDevPPM2LineEdit.setStyleSheet(le_readonly_bold_style)

        self.StdDevMeanPPMLineEdit = QLineEdit(parent=self.centralwidget)
        self.StdDevMeanPPMLineEdit.setGeometry(QRect(self.col7x, 402, self.lbl_width, self.lbl_height))
        self.StdDevMeanPPMLineEdit.setReadOnly(True)
        self.StdDevMeanPPMLineEdit.setStyleSheet(le_readonly_bold_style)
        self.C1C2LineEdit = QLineEdit(parent=self.centralwidget)
        self.C1C2LineEdit.setGeometry(QRect(self.col7x, 457, self.lbl_width, self.lbl_height))
        self.C1C2LineEdit.setReadOnly(True)
        self.C1C2LineEdit.setStyleSheet(le_readonly_bold_style)
        self.RatioMeanLineEdit = QLineEdit(parent=self.centralwidget)
        self.RatioMeanLineEdit.setGeometry(QRect(self.col7x, 512, self.lbl_width, self.lbl_height))
        self.RatioMeanLineEdit.setReadOnly(True)
        self.RatioMeanLineEdit.setStyleSheet(le_readonly_bold_style)
        self.le_ratioStdMean = QLineEdit(parent=self.centralwidget)
        self.le_ratioStdMean.setGeometry(QRect(self.col7x, 567, self.lbl_width, self.lbl_height))
        self.le_ratioStdMean.setReadOnly(True)
        self.le_ratioStdMean.setStyleSheet(le_readonly_bold_style)
        # self.SampUsedLineEdit = QLineEdit(parent=self.centralwidget)
        # self.SampUsedLineEdit.setGeometry(QRect(self.col7x, self.coly*11, self.lbl_width, self.lbl_height))
        # self.SampUsedLineEdit.setReadOnly(False)
        # self.SampUsedLineEdit.returnPressed.connect(self.changedSamplesUsed)
        self.IgnoredFirstLineEdit = QLineEdit(parent=self.centralwidget)
        self.IgnoredFirstLineEdit.setGeometry(QRect(self.col7x, 622, self.lbl_width, self.lbl_height))
        self.IgnoredFirstLineEdit.setReadOnly(False)
        self.IgnoredFirstLineEdit.setStyleSheet(le_style)
        self.IgnoredFirstLineEdit.returnPressed.connect(self.changedIgnoredFirst)

        self.IgnoredLastLineEdit = QLineEdit(parent=self.centralwidget)
        self.IgnoredLastLineEdit.setGeometry(QRect(self.col7x, 677, self.lbl_width, self.lbl_height))
        self.IgnoredLastLineEdit.setReadOnly(False)
        self.IgnoredLastLineEdit.setStyleSheet(le_style)
        self.IgnoredLastLineEdit.returnPressed.connect(self.changedIgnoredLast)

        self.le_error = QLineEdit(parent=self.centralwidget)
        self.le_error.setGeometry(QRect(self.col7x, 732, self.lbl_width, self.lbl_height))
        self.le_error.setReadOnly(True)
        self.le_error.setStyleSheet(
                """QLineEdit { background-color: rgb(215, 214, 213); color: red; font-weight: bold }""")

        self.le_Bfield = QLineEdit(parent=self.SetResTab)
        self.le_Bfield.setGeometry(QRect(self.col4x, 730, self.lbl_width - 70, self.lbl_height))
        self.le_Bfield.setReadOnly(False)
        self.le_Bfield.setHidden(True)
        self.le_Bfield.setValidator(float_validator())
        self.le_Bfield.setStyleSheet(le_style)

        self.le_sampleTemp = QLineEdit(parent=self.SetResTab)
        self.le_sampleTemp.setGeometry(QRect(self.col4x+46, 730, self.lbl_width - 48, self.lbl_height))
        self.le_sampleTemp.setReadOnly(False)
        self.le_sampleTemp.setHidden(True)
        self.le_sampleTemp.setValidator(float_validator())
        self.le_sampleTemp.setStyleSheet(le_style)

        self.le_contact = QLineEdit(parent=self.SetResTab)
        self.le_contact.setGeometry(QRect(self.col4x+114, 730, self.lbl_width - 41, self.lbl_height))
        self.le_contact.setReadOnly(False)
        self.le_contact.setHidden(True)
        self.le_contact.setStyleSheet(le_style)

        self.le_carrier_density = QLineEdit(parent=self.SetResTab)
        self.le_carrier_density.setGeometry(QRect(self.col4x+290, 730, self.lbl_width - 55, self.lbl_height))
        self.le_carrier_density.setReadOnly(False)
        self.le_carrier_density.setHidden(True)
        self.le_carrier_density.setValidator(float_validator())
        self.le_carrier_density.setStyleSheet(le_style)

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
        self.chb_qhr.setToolTip('')
        self.chb_detrend.setToolTip('')

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
        self.R1STPLineEdit.setToolTip('Value of the primary resistor at standard temperature and pressure (STP) based on the resistance database entry')
        self.R2STPLineEdit.setToolTip('Value of the secondary resistor at standard temperature and pressure (STP) based on the resistance database entry')
        self.NLineEdit.setToolTip('Total number of measurements or total number of full cycles')
        self.StdDevPPMLineEdit.setToolTip('Standard deviation of the resistance calculated from the raw .txt file')
        self.StdDevChkPPMLineEdit.setToolTip('Standard deviation of the resistance calculated from the _bvd.txt file')
        self.ppmMeanLineEdit.setToolTip('Mean resistance value calculated from the raw .txt file and corrected to standard temperature and pressure (STP)')
        self.RMeanChkPPMLineEdit.setToolTip('Mean resistance value calculated from the _bvd.txt file and corrected to standard temperature and pressure (STP)')
        self.RatioMeanLineEdit.setToolTip('Mean of the Ratio  R<sub>1</sub>/R<sub>2</sub>')
        self.le_ratioStdMean.setToolTip('Standard deviation of the mean of the Ratio R<sub>1</sub>/R<sub>2</sub>')
        self.IgnoredFirstLineEdit.setToolTip('Set the number of ignored first mesurements in every half cycle')
        self.IgnoredLastLineEdit.setToolTip('Set the number of ignored last mesurements in every half cycle')
        self.le_error.setToolTip('R Mean - R Mean Chk in ppb (n' + chr(937) + '/' + chr(937) + ')')
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
        self.chb_qhr.setToolTip('Check if characterizing a quantum Hall standard')
        self.chb_detrend.setToolTip('Quad Corr: remove the quadratic drift of the bridge voltage, fitted over 2 cycles together with the current reversal step. ' + \
                                    'No-Overlap: the windows follow each other, Overlap: a window starts at every cycle (like the overlapping Allan deviation)')

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
        self.VerticalLayoutWidget.setGeometry(QRect(0, 5, winSizeH-125, winSizeV-75))
        self.VerticalLayout = QVBoxLayout(self.VerticalLayoutWidget)
        self.VerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.ccc_fig = Figure()
        self.ccc_canvas = FigureCanvas(self.ccc_fig)
        self.VerticalLayout.addWidget(self.ccc_canvas)
        self.CCCDiagram()

    def CCCDiagram(self, R1="", R2="", N1="", N2="", I1="", I2="", BVD="", Na="", RH="", RL="", Ia="") -> None:
        """Draws the CCC circuit diagram, annotated with the values of the loaded file (empty values are not shown)"""
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.ccc_fig.clear()
        ax = self.ccc_fig.add_axes((0, 0, 1, 1))
        try:
            draw_ccc_diagram(ax, R1, R2, N1, N2, I1, I2, BVD, Na, RH, RL, Ia)
        except Exception as e:
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + ' Error: ' + str(e))
            ax.clear()
            ax.imshow(plt.imread(base_dir + r'\data\ccc_diagram_default.png'))
            ax.set_axis_off()
        self.ccc_canvas.draw()

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
        self.BVDax2 = self.BVDfig.add_subplot(2, 8, (1, 8)) # resistance
        self.BVDax3 = self.BVDfig.add_subplot(2, 8, (15, 16))  # histogram
        self.BVDax4 = self.BVDfig.add_subplot(2, 8, (9, 14) ) # bvd
        self.BVDfig.set_tight_layout(True)

        self.BVDax2.tick_params(which='both', direction='in')
        self.BVDax2.tick_params(axis='y', colors='b')
        self.BVDax2.set_axisbelow(True)
        self.BVDax2.grid(axis='both', zorder=2, which='both')
        self.BVDax2.xaxis.set_major_locator(MaxNLocator(integer=True))
        # self.BVDax2.xaxis.set_minor_locator(MultipleLocator(2))
        
        self.BVDax2twiny = self.BVDax2.twiny()
        self.BVDax2twiny.tick_params(which='both', direction='in')
        self.BVDax2twiny.tick_params(axis='y', colors='b')
        self.BVDax2twiny.set_axisbelow(True)
        self.BVDax2twiny.grid(axis='both', zorder=2, which='both')
        self.BVDax2twiny.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.BVDax2twiny.set_xlabel('Time [s]')
        # self.BVDax2twiny.xaxis.set_minor_locator(MultipleLocator(2))
        # box = self.BVDax2.get_position()
        # self.BVDax2.set_position([box.x0, box.y0 + box.height * 0.1,
        #          box.width, box.height * 0.9])

        self.BVDax4.tick_params(which='both', direction='in')
        self.BVDax4.tick_params(axis='y', colors='r')
        self.BVDax4.set_ylabel('BVD [V]', color='r')
        self.BVDax4.set_axisbelow(True)
        self.BVDax4.set_xlabel('Count')
        self.BVDax4.grid(axis='x', zorder=2, which='both')
        self.BVDax4.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.BVDax4.xaxis.set_minor_locator(MultipleLocator(2))

        self.BVDax3.tick_params(which='both', direction='in')
        self.BVDax3.tick_params(axis='y', colors='r')
        self.BVDax3.yaxis.tick_right()
        self.BVDax3.set_yticklabels([])
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
        self.SkewnessEdit.setFixedWidth(50)
        self.SkewnessEdit.setFixedHeight(20)
        self.SkewnessEdit.setStyleSheet(le_readonly_style)
        self.KurtosisEdit = QLineEdit(gridWidget)
        self.KurtosisEdit.setReadOnly(True)
        self.KurtosisEdit.setFixedWidth(50)
        self.KurtosisEdit.setFixedHeight(20)
        self.KurtosisEdit.setStyleSheet(le_readonly_style)
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
        self.AllanTypeComboBox.setCurrentText('all')
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
        self.OverlappingComboBox.setCurrentText('overlapping')
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
        # QRect()
        grid = QGridLayout(gridWidget)
        grid.setSpacing(0)

        lbl_lag_bvd = QLabel('Lag of BVD', parent=gridWidget)
        self.le_lag_bvd = QLineEdit(gridWidget)
        self.le_lag_bvd.setReadOnly(True)
        self.le_lag_bvd.setFixedWidth(90)
        self.le_lag_bvd.setFixedHeight(20)
        self.le_lag_bvd.setStyleSheet(le_readonly_style)

        lbl_alpha_bvd = QLabel('Alpha [BVD]', parent=gridWidget)
        self.le_alpha_bvd= QLineEdit(gridWidget)
        self.le_alpha_bvd.setReadOnly(True)
        self.le_alpha_bvd.setFixedWidth(90)
        self.le_alpha_bvd.setFixedHeight(20)
        self.le_alpha_bvd.setStyleSheet(le_readonly_style)

        lbl_lag_bva = QLabel('Lag of I-', parent=gridWidget)
        self.le_lag_bva = QLineEdit(gridWidget)
        self.le_lag_bva.setReadOnly(True)
        self.le_lag_bva.setFixedWidth(90)
        self.le_lag_bva.setFixedHeight(20)
        self.le_lag_bva.setStyleSheet(le_readonly_style)

        lbl_alpha_bva = QLabel('Alpha [I-]', parent=gridWidget)
        self.le_alpha_bva= QLineEdit(gridWidget)
        self.le_alpha_bva.setReadOnly(True)
        self.le_alpha_bva.setFixedWidth(90)
        self.le_alpha_bva.setFixedHeight(20)
        self.le_alpha_bva.setStyleSheet(le_readonly_style)

        lbl_lag_bvb = QLabel('Lag of I+', parent=gridWidget)
        self.le_lag_bvb = QLineEdit(gridWidget)
        self.le_lag_bvb.setReadOnly(True)
        self.le_lag_bvb.setFixedWidth(90)
        self.le_lag_bvb.setFixedHeight(20)
        self.le_lag_bvb.setStyleSheet(le_readonly_style)

        lbl_alpha_bvb = QLabel('Alpha [I+]', parent=gridWidget)
        self.le_alpha_bvb= QLineEdit(gridWidget)
        self.le_alpha_bvb.setReadOnly(True)
        self.le_alpha_bvb.setFixedWidth(90)
        self.le_alpha_bvb.setFixedHeight(20)
        self.le_alpha_bvb.setStyleSheet(le_readonly_style)
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

        self.chb_qhr = QCheckBox("QHR Char", parent=self.centralwidget)
        self.chb_qhr.setGeometry(QRect(self.col7x, int(self.coly*2.5), self.lbl_width - 10, int(self.lbl_height*1.2)))
        self.chb_qhr.setTristate(False)
        self.chb_qhr.setCheckState(Qt.CheckState.Unchecked)
        self.chb_qhr.stateChanged.connect(self.qhrChar)
        
        # quadratic drift correction (Quad Corr) of the bridge voltage, internally called detrend
        self.chb_detrend = QCheckBox("Quad Corr:\nNone", parent=self.centralwidget)
        self.chb_detrend.setGeometry(QRect(self.col7x, 760, self.lbl_width - 10, 38)) # two lines: name and mode
        self.chb_detrend.setTristate(True)
        self.chb_detrend.setCheckState(Qt.CheckState.Unchecked)
        self.chb_detrend.stateChanged.connect(self.detrend)

        self.saveButton = QPushButton(parent=self.centralwidget)
        self.saveButton.setGeometry(QRect(self.col7x, self.coly*3, self.lbl_width - 10, int(self.lbl_height*1.2)))
        self.saveButton.setEnabled(False)
        self.saveButton.clicked.connect(self.saveMDSS)
        
    def detrend(self, state) -> None:
        if state == 0:
            self.chb_detrend.setText("Quad Corr:\nNone")
            self.detrend_state = 0
        elif state == 1:
            self.chb_detrend.setText("Quad Corr:\nNo-Overlap")
            self.detrend_state = 1
        elif state == 2:
            self.chb_detrend.setText("Quad Corr:\nOverlap")
            self.detrend_state = 2
        self.getData()

    def qhrChar(self, state) -> None:
        if state == 2:
            self.qhrCharFlag = True
            self.lbl_Bfield.setHidden(False)
            self.le_Bfield.setHidden(False)
            self.lbl_sampleTemp.setHidden(False)
            self.le_sampleTemp.setHidden(False)
            self.lbl_contact.setHidden(False)
            self.le_contact.setHidden(False)
            self.lbl_qhr_system.setHidden(False)
            self.cb_qhr_system.setHidden(False)
            self.lbl_carrier_density.setHidden(False)
            self.le_carrier_density.setHidden(False)
        else:
            self.qhrCharFlag = False
            self.lbl_Bfield.setHidden(True)
            self.le_Bfield.setHidden(True)
            self.lbl_sampleTemp.setHidden(True)
            self.le_sampleTemp.setHidden(True)
            self.lbl_contact.setHidden(True)
            self.le_contact.setHidden(True)
            self.lbl_qhr_system.setHidden(True)
            self.cb_qhr_system.setHidden(True)
            self.lbl_carrier_density.setHidden(True)
            self.le_carrier_density.setHidden(True)

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

        self.cb_qhr_system = QComboBox(parent=self.SetResTab)
        self.cb_qhr_system.setGeometry(QRect(self.col4x+189, 730, self.lbl_width-15, self.lbl_height))
        self.cb_qhr_system.setEditable(False)
        self.cb_qhr_system.setHidden(True)
        self.cb_qhr_system.addItem('Cryomag-5T')
        self.cb_qhr_system.addItem('CMag-9T')
        self.cb_qhr_system.addItem('CMag-9T-N4')
        self.cb_qhr_system.addItem('Janis-SVT-9T')
        self.cb_qhr_system.addItem('BF-LD400')
        self.cb_qhr_system.addItem('Cryogenics-3He')

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
        # self.CommentsTextBrowser.setStyleSheet()

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
        self.lbl_error.setText(_translate("mainWindow", f"R Mean {chr(8722)} Chk [ppb]"))
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
        self.lbl_Bfield.setText(_translate("mainWindow", "B [T]"))
        self.lbl_sampleTemp.setText(_translate("mainWindow", "Samp. T [K]"))
        self.lbl_contact.setText(_translate("mainWindow", "[I+, I-, V+, V-]"))
        self.lbl_qhr_system.setText(_translate("mainWindow", "QHR System"))
        self.lbl_carrier_density.setText(_translate("mainWindow", "n [cm<sup>-2</sup>]"))

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

            if self.plottedRaw:
                self.clearRawPlot()
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
            if self.corr_bvdList:
                BVDmean = mean(self.corr_bvdList)
                BVDstd  = std(self.corr_bvdList, ddof=1)
                upper   =  3*BVDstd + BVDmean
                lower   = -3*BVDstd + BVDmean
                if len(self.corr_bvdList) > 1:
                    self.bvdfit = polyfit(array(self.bvdCount), array(self.corr_bvdList), deg=1, full=True)
                else:
                    self.bvdfit = ([nan, nan],) # a line fit needs at least two points
                # print(self.bvdfit[0][1])
                # print(self.bvdfit)
                self.bvdfitList = []
                for i in self.bvdCount:
                    self.bvdfitList.append(self.bvdfit[0][0]*i + self.bvdfit[0][1])  

                if self.plottedBVD:
                    self.clearBVDPlot()
                    if self.RButStatus == 'R1':
                        self.BVDax21_ref[0].set_data(self.bvdCount, self.R1List)
                        self.BVDax22_ref.set_ydata((self.meanR1,))
                        self.BVDax21twiny_ref[0].set_data(array(self.bvdCount)*float(self.dat.fullCyc), self.R1List)
                    else:
                        self.BVDax21_ref[0].set_data(self.bvdCount, self.R2List)
                        self.BVDax22_ref.set_ydata((self.meanR2,))
            
                    self.BVDax41_ref[0].set_data(self.bvdCount, self.corr_bvdList)
                    self.BVDax42_ref[0].set_data(self.bvdCount, upper*ones(len(self.corr_bvdList), dtype=int))
                    self.BVDax43_ref[0].set_data(self.bvdCount, lower*ones(len(self.corr_bvdList), dtype=int))
                    self.BVDax44_ref[0].set_data(self.bvdCount, self.bvdfitList)
    
                    self.BVDax3.hist(self.corr_bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                    self.BVDax3.set_ylim([self.BVDax4.get_ylim()[0], self.BVDax4.get_ylim()[1]])
                else:
                    if self.RButStatus == 'R1':
                        self.BVDax21_ref = self.BVDax2.plot(self.bvdCount, self.R1List, marker='o', ms=4, mfc='blue', mec='blue', ls='', alpha=self.alpha)
                        self.BVDax22_ref = self.BVDax2.axhline(y=self.meanR1, color='blue', ls='-', alpha=self.alpha-0.3, label='Mean')
                        self.BVDax21twiny_ref = self.BVDax2twiny.plot(array(self.bvdCount)*float(self.dat.fullCyc), self.R1List, marker='o', ms=4, mfc='blue', mec='blue', ls='', alpha=self.alpha, label= 'Resistance')
                    else:
                        self.BVDax21_ref = self.BVDax2.plot(self.bvdCount, self.R2List, marker='o', ms=4, mfc='blue', mec='blue', ls='', alpha=self.alpha)
                        self.BVDax22_ref = self.BVDax2.axhline(y=self.meanR2, color='blue', ls='-', alpha=self.alpha-0.3, label='Mean')
                        self.BVDax21twiny_ref = self.BVDax2twiny.plot(array(self.bvdCount)*float(self.dat.fullCyc), self.R2List, marker='o', ms=4, mfc='blue', mec='blue', ls='', alpha=self.alpha, label= 'Resistance')
                    self.BVDax41_ref = self.BVDax4.plot(self.bvdCount, self.corr_bvdList, marker='o', ms=4, mfc='red', mec='red', ls='', alpha=self.alpha, label= 'BVD [V]')
                    self.BVDax42_ref = self.BVDax4.plot(self.bvdCount, upper*ones(len(self.corr_bvdList), dtype=int), marker='', color='red', ms=0, ls='--', alpha=self.alpha)
                    self.BVDax43_ref = self.BVDax4.plot(self.bvdCount, lower*ones(len(self.corr_bvdList), dtype=int), marker='', color='red', ms=0, ls='--', alpha=self.alpha)
                    self.BVDax44_ref = self.BVDax4.plot(self.bvdCount, self.bvdfitList, color = 'red', ls='-', alpha=self.alpha - 0.3)

                    self.BVDax3.hist(self.corr_bvdList, bins=self.bins, orientation='horizontal', color='r', edgecolor='k')
                    self.BVDax3.set_ylim([self.BVDax4.get_ylim()[0], self.BVDax4.get_ylim()[1]])
                # mean with overlapping quadratic drift removal next to the mean of the current Quad Corr setting
                if self.RButStatus == 'R1':
                    meanR, meanR_overlap = self.meanR1, self.meanR1_overlap
                else:
                    meanR, meanR_overlap = self.meanR2, self.meanR2_overlap
                if self.plottedBVD:
                    self.BVDax23_ref.set_ydata((meanR_overlap,))
                else:
                    self.BVDax23_ref = self.BVDax2.axhline(y=meanR_overlap, color='#eb6834', ls='--', alpha=0.8)
                mean_label = {0: 'Mean', 1: 'Mean, Quad Corr No-Overlap', 2: 'Mean, Quad Corr Overlap'}[self.detrend_state]
                self.BVDax22_ref.set_label(mean_label + ': ' + str("{:.3f}".format(meanR)))
                # with Quad Corr: Overlap selected both lines are the same, so only one is shown
                self.BVDax23_ref.set_visible(self.detrend_state != 2)
                self.BVDax23_ref.set_label('_nolegend_' if self.detrend_state == 2 else 'Mean, Quad Corr Overlap: ' + str("{:.3f}".format(meanR_overlap)))
                self.BVDax2.legend(loc='upper right', fancybox=True, shadow=True, ncols=2, columnspacing=1, fontsize=10)
                self.slope_text = self.BVDax4.text(x=0.05, y=0.1, s='Slope: ' + str("{:.3f}".format((self.bvdfit[0][0]*1e9)/float(self.dat.fullCyc))) + ' nV/s', color='red', transform=self.BVDax4.transAxes)
                # Put a legend below current axis
                # lines, labels   = self.BVDax2.get_legend_handles_labels()
                # lines2, labels2 = self.BVDax4.get_legend_handles_labels()
                # self.BVDax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.2),
                #                    fancybox=True, shadow=True, ncols=2, columnspacing=0)
                if self.RButStatus == 'R1':
                    self.BVDax2.set_ylabel(r'$R_{2}$' + f' [{chr(956)}{chr(937)}/{chr(937)}]', color='b')
                else:
                    self.BVDax2.set_ylabel(r'$R_{1}$' + f' [{chr(956)}{chr(937)}/{chr(937)}]', color='b')
                # self.BVDax21 = self.BVDax2.secondary_xaxis('top', functions = (lambda x: x*float(self.dat.fullCyc) , lambda x: x/float(self.dat.fullCyc)))
                # self.BVDax21.set_xlabel('Time [s]')
                # self.BVDax21.tick_params(which='both', direction='in')
                # self.BVDax21.xaxis.set_major_locator(MaxNLocator(integer=True))
                
                self.BVDax2.relim()
                self.BVDax2.autoscale(tight=None, axis='both', enable=True)
                self.BVDax2.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDax2twiny.relim()
                self.BVDax2twiny.autoscale(tight=None, axis='both', enable=True)
                self.BVDax2twiny.autoscale_view(tight=None, scalex=True, scaley=True)
                # self.BVDax21.set_xlim(array(self.BVDax2.get_xlim())*float(self.dat.fullCyc))
                # self.BVDax21.set_xticks(array(self.BVDax2.get_xticks())*float(self.dat.fullCyc))
                # self.BVDax21.relim()
                # self.BVDax21.autoscale(tight=None, axis='both', enable=True)
                # self.BVDax21.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDax4.relim()
                self.BVDax4.autoscale(tight=None, axis='both', enable=True)
                self.BVDax4.autoscale_view(tight=None, scalex=True, scaley=True)
                self.BVDax3.set_ylim([self.BVDax4.get_ylim()[0], self.BVDax4.get_ylim()[1]])
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
                self.BVDax41_ref[0].set_data(array([]), array([]))
                self.BVDax42_ref[0].set_data(array([]), array([]))
                self.BVDax43_ref[0].set_data(array([]), array([]))
                self.BVDax44_ref[0].set_data(array([]), array([]))
                self.BVDax21_ref[0].set_data(array([]), array([]))
                self.BVDax22_ref.set_ydata((array([]),))
                self.BVDax21twiny_ref[0].set_data(array([]), array([]))
                self.slope_text.remove()
                for container in self.BVDax3.containers:
                    container.remove()
                self.BVDax23_ref.set_ydata((array([]),))
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
            self.dat = magnicon_ccc(self.txtFilePath, dbdir, site, mysql_config)

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
            # total pressures of this file, before they kept the value of the previous file (or a typed-in
            # pressure) when there is no environment path
            self.R1TotPres = self.R1pres + self.R1OilPres
            self.R2TotPres = self.R2pres + self.R2OilPres
            # self.SampUsedLineEdit.setText(str(self.dat.samplesUsed))
            self.IgnoredFirstLineEdit.setText(str(self.dat.ignored_first))
            self.IgnoredLastLineEdit.setText(str(self.dat.ignored_last))
            # a (re)loaded file starts with all its cycles and without the values typed by the user
            self.deletedCycles      = []
            self.SampUsedCt         = 0
            self.changedDeltaI2R2Ct = 0
            self.changedR1STPBool   = False
            self.changedR2STPBool   = False
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
                if self.batchMode:
                    # batch processing plots only the last file and skips the ADEV and PSD, see batchProcess
                    return
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
                # draw the diagram for this file now if its tab is showing, otherwise when the tab is opened
                self.draw_flag = False
                if self.tabWidget.currentIndex() == 0:
                    self.updateCCCDiagram()

                # print("Time taken to plot allan and spectrum: ", perf_counter() - plotStat_start)
                # getPlot_end = perf_counter() - getData_start
                # print("Time taken to plot all data in GUI: ", str(getPlot_end))
                getData_end = perf_counter() - getData_start
                # print("Time taken to get and analyze data: " +  str(getData_end))
                self.statusbar.showMessage('Time taken to process and display data ' + str("{:2.2f}".format(getData_end)) + ' s', 5000)
                if self.user_warn_msg != "":
                    self.show_warning_dialog()
            else:
                self.setInvalidData()
                if not self.batchMode:
                    self.statusbar.showMessage('Invalid file selected...', 2000)
                # self.clearPlots()
        else:
            # self.clearPlots()
            self.setInvalidData()
            if not self.batchMode:
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
            # print(self.chb_detrend.checkState())
            self.bvd_stat_obj = bvd_stat(self.txtFilePath, int(self.IgnoredFirstLineEdit.text()), \
                                         int(self.IgnoredLastLineEdit.text()), self.dat, debug_mode, \
                                         self.detrend_state)
            self.bvdList, self.V1_all, self.V2_all, self.A, self.B, self.stdA, self.stdB, self.AA, self.BB, self.stdbvdList_all, self.AA_used, self.BB_used = self.bvd_stat_obj.send_bvd_stats()
            self.bvd_stat_obj.clear_bvd_stats()
        except Exception as e:
            logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                           ' Error: ' + str(e))
            self.bvdList, self.V1_all, self.V2_all, self.A, self.B, self.stdA, self.stdB, self.AA, self.BB, self.stdbvdList_all, self.AA_used, self.BB_used = [], [], [], [], [], [], [], [], [], [], [], []
            pass
        # BVD with overlapping quadratic drift removal (Quad Corr: Overlap) for the second mean line in the R plot
        if self.detrend_state == 2:
            self.bvdList_overlap_all = self.bvdList
        else:
            try:
                self.bvdList_overlap_all = bvd_stat(self.txtFilePath, int(self.IgnoredFirstLineEdit.text()), \
                                                    int(self.IgnoredLastLineEdit.text()), self.dat, debug_mode, 2).bvdList
            except Exception as e:
                logger.warning('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                               ' Error: ' + str(e))
                self.bvdList_overlap_all = []
        # this comes from _bvd.txt files, copied so deleting cycles never changes the parsed file data
        self.bvdList_chk_all = list(self.dat.bvd)
        # cycles more than 3 sigma away from the mean BVD are left out of the results
        self.outlierCycles = set()
        if self.outliers and len(self.bvdList) > 1:
            BVDmean = mean(self.bvdList)
            BVDstd  = std(self.bvdList, ddof=1)
            self.outlierCycles = {i for i, bvd in enumerate(self.bvdList) if abs(bvd - BVDmean) > 3*BVDstd}
        self.selectCycles()

    def selectCycles(self, keepSelection: bool = False) -> None:
        """Makes the per-cycle lists used in the results and plots from the lists for all the cycles,
           leaving out the outlier cycles and the cycles deleted by the user. All the lists are made
           here with the same cycles so they always stay aligned.
        Parameters
        ----------
        keepSelection : bool, stay on the selected cycle in the delete list (after a delete or restore)
        Returns
        -------
        None
        """
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        excluded            = self.outlierCycles.union(self.deletedCycles)
        self.bvdCount       = [i for i in range(len(self.bvdList)) if i not in excluded]
        self.corr_bvdList   = [self.bvdList[i] for i in self.bvdCount]
        self.V1             = [self.V1_all[i] for i in self.bvdCount]
        self.V2             = [self.V2_all[i] for i in self.bvdCount]
        self.stdbvdList     = [self.stdbvdList_all[i] for i in self.bvdCount]
        self.bvdList_chk    = [bvd for i, bvd in enumerate(self.bvdList_chk_all) if i not in excluded]
        self.bvdList_overlap = [bvd for i, bvd in enumerate(self.bvdList_overlap_all) if i not in excluded]
        # list the cycles that can be deleted, last cycle first
        selected = self.plotCountCombo.currentText()
        position = self.plotCountCombo.currentIndex()
        self.plotCountCombo.clear()
        self.plotCountCombo.addItems([f'ct {i}' for i in reversed(self.bvdCount)])
        if keepSelection:
            # stay on the same cycle, or on the one that took the place of a deleted cycle
            index = self.plotCountCombo.findText(selected)
            self.plotCountCombo.setCurrentIndex(index if index >= 0 else min(position, self.plotCountCombo.count() - 1))

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
        self.R1List_nocorr      = []
        self.R2List_nocorr      = []
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
                self.R1List_nocorr.append(float(((((self.R1*(1./rm))/mag.R2NomVal) - 1) * 10**6)))
                self.C1R1List.append((self.R1/rmC1 - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
                self.C2R1List.append((self.R1/rmC2 - mag.R2NomVal)/mag.R2NomVal * 10**6 - R2corr)
            except ZeroDivisionError:
                self.R1List.append(0)
                self.R1List_nocorr.append(0)
                self.C1R1List.append(0)
                self.C2R1List.append(0)
                pass
            try:
                self.R2List.append(float(((((self.R2*rm)/mag.R1NomVal) - 1) * 10**6) - R1corr)) # this is actually R1List
                self.R2List_nocorr.append(float(((((self.R2*rm)/mag.R1NomVal) - 1) * 10**6)))
                self.C1R2List.append((self.R2*rmC1 - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
                self.C2R2List.append((self.R2*rmC2 - mag.R1NomVal)/mag.R1NomVal * 10**6 - R1corr)
            except ZeroDivisionError:
                self.R2List.append(0)
                self.R2List_nocorr.append(0)
                self.C1R2List.append(0)
                self.C2R2List.append(0)
        # the same resistance means with the BVD after overlapping quadratic drift removal (Quad Corr: Overlap), for the R plot
        R1List_overlap, R2List_overlap = [], []
        for bvd in self.bvdList_overlap:
            try:
                rm = compensation*(1 + (bvd/myDeltaI2R2))
                R1List_overlap.append(float(((((self.R1*(1./rm))/mag.R2NomVal) - 1) * 10**6) - R2corr)) # this is actually R2
                R2List_overlap.append(float(((((self.R2*rm)/mag.R1NomVal) - 1) * 10**6) - R1corr)) # this is actually R1
            except ZeroDivisionError:
                pass
        self.meanR1_overlap = mean(R1List_overlap) if R1List_overlap else nan
        self.meanR2_overlap = mean(R2List_overlap) if R2List_overlap else nan
        # print(self.R1List, mean(self.R1List), len(self.R1List))
        if self.ratioMeanList != []:
            # self.ratioMean = compensation*(1 + (self.bvd_mean/myDeltaI2R2)) # calculated from raw bridge voltages
            self.ratioMean = mean(self.ratioMeanList)
            self.ratioStdMean = std(self.ratioMeanList, ddof=1)/sqrt(len(self.ratioMeanList))
            self.meanR1     = mean(self.R1List) # this is mean of R2
            self.meanR1_nocorr = mean(self.R1List_nocorr)
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
            self.meanR2_nocorr = mean(self.R2List_nocorr)
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
            self.meanR1_nocorr  = nan
            self.meanR2_nocorr  = nan
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
                # self.R1MeanChkList_nocorr.append((((self.R1/j) - mag.R2NomVal)/mag.R2NomVal) * 10**6)
                self.R2MeanChkList.append(((self.R2*j - mag.R1NomVal)/mag.R1NomVal) * 10**6 - R1corr) # this is actually R1
                # self.R2MeanChkList_nocorr.append(((self.R2*j - mag.R1NomVal)/mag.R1NomVal) * 10**6)
                
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
        global __version__
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.VMeanLineEdit.setText(str("{:.9e}".format(self.bvd_mean)))
        self.VMeanChkLineEdit.setText(str("{:.9e}".format(self.bvd_mean_chk)))
        self.Current1LineEdit.setText(str(self.dat.I1))
        self.FullCycLineEdit.setText(str(self.dat.fullCyc))
        # warnings about the file's settings, rebuilt on every update so each one is listed once
        self.user_warn_msg = ""
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
        if str(self.dat.screenVolt) == '0':
            self.user_warn_msg += "Screen voltage is off!\n"
        if self.dat.dbWarning != '':
            self.user_warn_msg += self.dat.dbWarning + "\n"
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
        self.RelHumLineEdit.setText(str(self.dat.relHum))
        self.kLineEdit.setText(str("{:.12f}".format(self.k)))
        if self.k == 0:
            self.kLineEdit.setStyleSheet(red_style)
        else:
            self.kLineEdit.setStyleSheet(le_readonly_style)
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

        self.deletedCycles      = []
        self.outlierCycles      = set()
        self.bvdCount           = []
        self.corr_bvdList       = [] # nothing to plot, e.g. when the Standard R button is clicked
        self.bvdfitList         = []
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
            # print('R1: ', self.meanR1_nocorr)
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
            self.CommentsTextBrowser.setText(self.dat.comments + ', Ratio: ' + str(self.ratioMean) + ' +/- ' + str(self.ratioStdMean) + ', C not at STP [ppm]: ' + str("{:.7f}".format(self.meanR1_nocorr)) + ', MOA Version: ' + __version__)
            err = (self.meanR1 - self.R1MeanChk)*1e3
            self.le_error.setText(str("{:.9f}".format(err)))
            if self.R1PPM:
                self.R1PPMLineEdit.setText(str("{:2.7f}".format(self.R1PPM)))
            else:
                self.R1PPMLineEdit.setText(str(0))
        else:
            # print('R2: ', self.meanR2_nocorr)
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
            self.CommentsTextBrowser.setText(self.dat.comments + ', Ratio: ' + str(self.ratioMean) + ' +/- ' + str(self.ratioStdMean) + ', C not at STP [ppm]: ' + str("{:.7f}".format(self.meanR2_nocorr)) + ', MOA Version: ' + __version__)
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
            self.R1PresLineEdit.setText(str("{:.4f}".format(self.R1pres)))
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
            self.R2PresLineEdit.setText(str("{:.4f}".format(self.R2pres)))
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
            self.txtFileLineEdit.setText(self.txtFilePath)
            self.validFile = False
            self.chb_outlier.setCheckState(Qt.CheckState.Unchecked)
            self.chb_qhr.setCheckState(Qt.CheckState.Unchecked)
            self.outliers=False
            self.draw_flag = False
            self.qhrCharFlag = False
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

    def mdssDirectory(self, txtFilePath: str) -> str:
        """Folder the pymdss file of txtFilePath is saved to, the Transfer Files folder on the desktop at NIST
           (created if needed), otherwise the folder of the data file
        """
        mdssdir = ""
        if site == 'NIST':
            mdssdir = "C:" + os.sep + "Users" + os.sep + os.getlogin() + os.sep + "Desktop" + os.sep + r"Transfer Files"
            if not os.path.isdir(mdssdir):
                os.mkdir(mdssdir)
        else:
            tempdir = txtFilePath.split('/')
            tempdir.pop(-1)
            for i in tempdir:
                mdssdir = mdssdir + i + os.sep
        return mdssdir

    def saveMDSS(self) -> None:
        global red_style
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        self.mdssdir = self.mdssDirectory(self.txtFilePath)
        # self.progressBar.setProperty('value', 25)

        # self.dat.comments = self.CommentsTextBrowser.toPlainText()
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
                      comments = self.CommentsTextBrowser.toPlainText(), bfield=self.le_Bfield.text(), sampleTemp=self.le_sampleTemp.text(), contact=self.le_contact.text(), qhr_system=self.cb_qhr_system.currentText(), carrier_density=self.le_carrier_density.text(), qhrchar=self.qhrCharFlag)
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

    def batchProcess(self) -> None:
        """Processes several data files with the current settings and saves the pymdss, _pyCCCRAW.mea and
           _pyBV.mea files of each one, as MDSS Save does. The settings (standard R, SQUID feedin, electronics,
           probe, oil depths, environment paths, Remove Outliers, Quad Corr and, when QHR Char is checked, the QHR
           values) are used for every file. The ignored samples, delta(I2R2) and STP predictions are those of
           each file. The ADEV and PSD are not calculated. The results are summarized in one csv file per batch,
           saved next to the data files.
        """
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        files, _ = QFileDialog.getOpenFileNames(mainWindow, "Select data files to batch process", \
                                                self.dialog.directory().absolutePath(), "Text files (*_bvd.txt)")
        if not files:
            return
        files = sorted(files)
        datadir = os.path.dirname(files[0])
        self.dialog.setDirectory(datadir)
        if self.qhrCharFlag:
            process = 'QHR Process (B [T]: ' + self.le_Bfield.text() + ', Samp. T [K]: ' + self.le_sampleTemp.text() + \
                      ', [I+, I-, V+, V-]: ' + self.le_contact.text() + ', QHR System: ' + self.cb_qhr_system.currentText() + \
                      ', n [cm^-2]: ' + self.le_carrier_density.text() + ')'
        else:
            process = 'Magnicon CCC Process'
        env1 = self.le_path_temperature1.text() if self.le_path_temperature1.text() != '' else 'none, temperature of each file and 101325 Pa'
        env2 = self.le_path_temperature2.text() if self.le_path_temperature2.text() != '' else 'none, temperature of each file and 101325 Pa'
        settings = {'Standard R': self.RButStatus, 'SQUID Feedin Polarity': self.SquidFeedStatus, \
                    'SQUID Feedin Arm': self.CurrentButStatus, 'Magnicon Electronics': self.MagElecComboBox.currentText(), \
                    'Probe': self.ProbeComboBox.currentText(), 'R1 Oil Depth [mm]': str(self.R1OilDepth), \
                    'R2 Oil Depth [mm]': str(self.R2OilDepth), 'R1 Environment Path': env1, 'R2 Environment Path': env2, \
                    'Remove Outliers': 'Yes' if self.outliers else 'No', \
                    'Quad Corr': {0: 'None', 1: 'No-Overlap', 2: 'Overlap'}[self.detrend_state], 'Process': process}
        mdssdir = self.mdssDirectory(files[0])
        msgBox = QMessageBox(QMessageBox.Icon.Question, 'Batch Process', 'Process and save ' + str(len(files)) + \
                             ' data files with these settings?', \
                             QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel, parent=mainWindow)
        msgBox.setInformativeText('\n'.join(k + ': ' + v for k, v in settings.items()) + '\n\n' + \
                                  'The ignored samples, ' + chr(916) + '(I2R2) and STP predictions of each file are used, ' + \
                                  'the ADEV and PSD are not calculated.\n\n' + \
                                  'pymdss files are saved to ' + os.path.normpath(mdssdir) + ', the .mea files and a summary ' + \
                                  'csv file next to the data files. Existing pymdss and .mea files of these runs are overwritten.')
        msgBox.exec()
        if msgBox.standardButton(msgBox.clickedButton()) != QMessageBox.StandardButton.Ok:
            return

        progress = QProgressDialog('', 'Cancel', 0, len(files), mainWindow)
        progress.setWindowTitle('Batch Process')
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        rows = []
        lastValid = ''
        self.batchMode = True
        try:
            for n, f in enumerate(files):
                progress.setLabelText('Processing ' + os.path.basename(f) + ' (' + str(n + 1) + ' of ' + str(len(files)) + ')')
                progress.setValue(n)
                if progress.wasCanceled():
                    break
                row = self.batchProcessFile(f)
                row.update({'Remove Outliers': settings['Remove Outliers'], 'Quad Corr': settings['Quad Corr'], \
                            'Process': 'QHR Process' if self.qhrCharFlag else 'Magnicon CCC Process'})
                rows.append(row)
                if self.validFile and self.txtFilePath == f:
                    lastValid = f
            progress.setValue(len(files))
            # show the last file that could be processed, with its raw and BVD plots
            if lastValid != '' and (not self.validFile or self.txtFilePath != lastValid):
                self.txtFilePath = lastValid
                self.txtFileLineEdit.setText(lastValid)
                self.getData()
        finally:
            self.batchMode = False
            progress.close()
        if self.validFile:
            self.plotRaw()
            self.plotBVD()
            self.draw_flag = False
            if self.tabWidget.currentIndex() == 0:
                self.updateCCCDiagram()
        # the ADEV and PSD tabs would show another file
        self.clearAllanPlot()
        self.clearSpecPlot()
        self.AllanCanvas.draw()
        self.SpecCanvas.draw()

        csvPath = os.path.join(datadir, 'pyBatch_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv')
        csvError = ''
        try:
            with open(csvPath, 'w', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=batch_csv_fields, restval='', extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            logger.error('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3], exc_info=True)
            csvError = 'The summary csv file could not be written: ' + str(e)

        saved = [r for r in rows if r['Status'] == 'Saved']
        notSaved = [r for r in rows if r['Status'] != 'Saved']
        text = str(len(saved)) + ' of ' + str(len(files)) + ' data files saved.'
        if len(rows) < len(files):
            text += '\nCanceled, ' + str(len(files) - len(rows)) + ' files were not processed.'
        if notSaved:
            text += '\n\nNot saved:\n' + '\n'.join(r['File'] + ': ' + r['Status'] + \
                                                   (' (' + r['Error'] + ')' if r.get('Error', '') != '' else '') for r in notSaved)
        warned = [r for r in rows if r.get('Warnings', '') != '']
        if warned:
            text += '\n\n' + str(len(warned)) + ' files have warnings, see the Warnings column of the summary.'
        text += '\n\n' + (csvError if csvError != '' else 'Summary: ' + os.path.normpath(csvPath))
        details = '\n'.join(r['File'] + ': ' + r['Status'] + \
                            (', ' + r['Warnings'] if r.get('Warnings', '') != '' else '') for r in rows)
        summaryBox = QMessageBox(QMessageBox.Icon.Information if not notSaved and csvError == '' else QMessageBox.Icon.Warning, \
                                 'Batch Process', text, parent=mainWindow)
        summaryBox.setDetailedText(details)
        self.statusbar.showMessage('Batch process: ' + str(len(saved)) + ' of ' + str(len(files)) + \
                                   ' data files saved, ADEV and PSD are not calculated in a batch', 10000)
        summaryBox.exec()

    def batchProcessFile(self, txtFilePath: str) -> dict:
        """Loads, processes and saves one data file of a batch. Returns its row of the summary csv file"""
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        row = {'File': os.path.basename(txtFilePath), 'Status': 'Error'}
        try:
            rawFile = txtFilePath.split('_bvd.txt')[0] + '.txt'
            if not os.path.exists(rawFile):
                row['Status'] = 'Raw data file ' + os.path.basename(rawFile) + ' not found'
                return row
            self.txtFilePath = txtFilePath
            self.txtFileLineEdit.setText(txtFilePath)
            self.validFile = False
            self.user_warn_msg = ""
            self.getData()
            if not self.validFile:
                row['Status'] = 'Invalid file'
                return row
            if self.RButStatus == 'R1':
                (meanR, stdR, stdMeanR, meanRChk, C1, C2) = (self.meanR1, self.stdR1ppm, self.stdMeanR1, \
                                                            self.R1MeanChk, self.C1R1, self.C2R1)
            else:
                (meanR, stdR, stdMeanR, meanRChk, C1, C2) = (self.meanR2, self.stdR2ppm, self.stdMeanR2, \
                                                            self.R2MeanChk, self.C1R2, self.C2R2)
            row.update({'Start Time': str(self.dat.startDate), 'End Time': str(self.dat.endDate), \
                        'Standard': self.RButStatus, 'R1 Serial': self.dat.R1SN, 'R2 Serial': self.dat.R2SN, \
                        'Mean [uOhm/Ohm]': meanR, 'Std. Dev. [uOhm/Ohm]': stdR, 'Std. Mean [uOhm/Ohm]': stdMeanR, \
                        'R Mean Chk [uOhm/Ohm]': meanRChk, 'R Mean - Chk [ppb]': (meanR - meanRChk)*1e3, \
                        'C1-C2 [uOhm/Ohm]': C1 - C2, 'Ratio Mean': self.ratioMean, 'Ratio Std. Mean': self.ratioStdMean, \
                        'BVD Mean [V]': self.bvd_mean, 'BVD Std. Mean [V]': self.bvd_stdMean, 'N': self.N, \
                        'Ignored First': self.IgnoredFirstLineEdit.text(), 'Ignored Last': self.IgnoredLastLineEdit.text(), \
                        'R1 Temperature [C]': self.R1Temp, 'R2 Temperature [C]': self.R2Temp, \
                        'R1 Total Pres. [Pa]': self.R1TotPres, 'R2 Total Pres. [Pa]': self.R2TotPres, \
                        'R1STPPred [uOhm/Ohm]': self.R1STPLineEdit.text(), 'R2STPPred [uOhm/Ohm]': self.R2STPLineEdit.text(), \
                        'Warnings': '; '.join(w for w in self.user_warn_msg.split('\n') if w != '')})
            self.saveMDSS()
            row['pymdss File'] = os.path.normpath(os.path.join(self.mdssdir, os.path.basename(txtFilePath).replace('_bvd.txt', '') + '_pyMDSS.txt'))
            row['Status'] = 'Saved'
        except Exception as e:
            logger.error('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3] + \
                         ' File: ' + txtFilePath, exc_info=True)
            row['Status'] = 'Error'
            row['Error'] = type(e).__name__ + ': ' + str(e)
            try:
                # do not show or plot the results of a file that failed part way
                self.setInvalidData()
            except Exception:
                self.validFile = False
        return row

    def cleanUp(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        # the deleted cycles and the values typed by the user (ignored samples, delta(I2R2), STP predictions)
        # are kept, they are only cleared when a file is (re)loaded
        self.outlierCycles      = set()

        self.bvdList            = []
        self.corr_bvdList       = []
        self.stdbvdList         = []
        self.bvdCount           = []
        self.bvdfitList         = []

        self.bvdList_chk        = []
        self.bvdList_overlap    = []

        self.CommentsTextBrowser.setText("")

    def deleteBut(self) -> None:
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.plottedBVD and self.plotCountCombo.count():
            # the delete list shows the cycle numbers of the cycles in use
            self.deletedCycles.append(int(self.plotCountCombo.currentText().replace('ct ', '')))
            self.selectCycles(keepSelection=True)
            self.results(self.dat, self.R1Temp, self.R2Temp, self.R1TotPres, self.R2TotPres)
            self.setValidData()
            self.plotBVD()
            self.plotAllan()

    def restoreDeleted(self) -> None:
        """Restore last deleted data point
        Returns
        -------
        None
        """
        if debug_mode:
            logger.debug('In class: ' + self.__class__.__name__ + ' In function: ' + inspect.stack()[0][3])
        if self.deletedCycles != []:
            self.deletedCycles.pop(-1)
            self.selectCycles(keepSelection=True)
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

def excepthook(exc_type, exc_value, exc_tb) -> None:
    """Logs unhandled exceptions and shows them in a dialog. Installed as sys.excepthook this
       also stops PyQt from aborting the program when an exception escapes a slot.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logger.error('Unhandled exception', exc_info=(exc_type, exc_value, exc_tb))
    try:
        msgBox = QMessageBox(QMessageBox.Icon.Critical, 'Error', exc_type.__name__ + ': ' + str(exc_value) + \
                             '\n\nThe last action did not complete. Details were written to the log file.', \
                             parent=QApplication.activeWindow())
        msgBox.setDetailedText(''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        msgBox.exec()
    except Exception:
        sys.__excepthook__(exc_type, exc_value, exc_tb)

if __name__ == "__main__":
    parser = ArgumentParser(prog = 'Magnicon-Offline-Analyzer',
                            description='Configure Magnicon-Offline-Analyzer',
                            epilog='A utility to interact with the analysis software for Magnicon CCC systems', add_help=True)
    parser.add_argument('-db', '--db_path', help='Specify resistor database directory', default="", type=str)
    parser.add_argument('-l', '--log_path', help='Specify log directory', default="C:" + os.sep + "_logcache_", type=dir_path)
    parser.add_argument('-d', '--debug', help='Debugging mode', action='store_true')
    parser.add_argument('-s', '--site', help='Site where this program is used', default="", type=str)
    parser.add_argument('-c', '--specific_gravity', help='Specific gravity of oil for oil type resistors', default=0.8465, type=float)
    parser.add_argument('--mysql_host', help='Host of the MySQL resistor database (table resistors_database), tried ' + \
                        'first with -s NIST before the ResDataBase.dat files', default=MYSQL_DEFAULTS['host'], type=str)
    parser.add_argument('--mysql_port', help='Port of the MySQL resistor database', default=MYSQL_DEFAULTS['port'], type=int)
    parser.add_argument('--mysql_user', help='User of the MySQL resistor database', default=MYSQL_DEFAULTS['user'], type=str)
    parser.add_argument('--mysql_password', help='Password of the MySQL resistor database, when not given it is read ' + \
                        'from the MYSQL_PWD environment variable', default=None, type=str)
    parser.add_argument('--mysql_db', help='Schema of the MySQL resistor database', default=MYSQL_DEFAULTS['database'], type=str)
    args, unk = parser.parse_known_args()
    if unk:
        logger.debug("Warning: Ignoring unknown arguments: {:}".format(unk))
        pass
    dbdir = args.db_path
    logdir = args.log_path
    debug_mode = args.debug
    site = args.site
    c = args.specific_gravity
    mysql_config = {'host': args.mysql_host, 'port': args.mysql_port, 'user': args.mysql_user, \
                    'password': args.mysql_password, 'database': args.mysql_db}
    # define the file handler and formatting
    lfname = logdir + os.sep + 'debug_magnicon-offline-analyzer' + '.log'
    file_handler = TimedRotatingFileHandler(lfname, when='midnight')
    fmt = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.info('MySQL resistor database: ' + mysql_config['user'] + '@' + mysql_config['host'] + ':' + \
                str(mysql_config['port']) + '/' + mysql_config['database'] + ', password ' + \
                ('given' if args.mysql_password is not None else 'from MYSQL_PWD' if os.environ.get('MYSQL_PWD') else 'not set'))
    app = QApplication(sys.argv)
    app.setStyle("windowsvista")
    sys.excepthook = excepthook # show unhandled exceptions in a dialog instead of letting PyQt abort
    mainWindow = QMainWindow()
    ui = Ui_mainWindow()
    ui.setupUi(mainWindow)
    mainWindow.show()
    sys.exit(app.exec())