
# info
__author__ 		=       "Andrew Geckle & Alireza Panna"
__copyright__ 	=       "This data is publicly available according to the NIST statements of copyright, fair use and licensing; see https://www.nist.gov/director/copyright-fair-use-and-licensing-statements-srd-data-and-software"
__license__ 	=       "NIST"
__maintainer__ 	=       "Alireza Panna"
__email__ 		=       "alireza.panna@nist.gov"
__status__ 		=       "Stable"
__date__        =       "06/2023"
<<<<<<< HEAD
__version__ 	=       "2.3.1"
=======
__version__ 	=       "2.3"
>>>>>>> d0c9b029c8fe3c268d685ba5d71039651f73f51f
__ChangeLog__   =       """
                        031224:     FIX: Make R1STPPPM and R2STPPPM linedits editable so user can update predicted value, add requirements.txt
                                    for building project, switch to using allantools for plotting allan deviations since its faster, add 
                                    this file, update to 1.4
                        031324:     ENH: Added autocorrelation (ACF) plots and ability to determine dominant power law noise in data, update
                                    to 1.5
                        031424:     FIX: apply fix for crash when bvd file has no data, mdss file save name changed. write _pyadev.txt, _pypsd.txt and pyCCCRAW.mea files
                        031524:     FIX: Add plot labels where necessary, fix more bugs, update to 1.6
                        031624:     ENH: Add timing diagram in Help menu, update to 1.6.1
                        032124:     ENH: Add start and end time line edits, fix I+ and I- labels in plot, update to 1.6.3
                        032924:     FIX: Fix crash when loading incomplete bvd files, update to 1.6.4
                        040924:     ENH: Add folder paths for temperature and calculate the average temperatures for R1 and R2 automatically, fix color issue
                                         with MDSS Save button, update to version 1.7
                        041024:     FIX: Remove unused imports, add more precision digits to temperature line edits, fix issues with checks and add some 
                                         tooltips, update to 1.8
                        041124:     ENH: Add show/hide tooltip submenu under help menu, fix timing diagram equation, update to 1.9
                        041324:     FIX: Fix filename for .mea file, fix pressure readout, update to 1.9.1
                        041324:     FIX: mdss files writes correct R1STP and R2STP prediction values if user changes them to be custom values.
                        042924:     ADD: new custom icon for the project, add ratio stdMean line edit, add ratio value to comment, set pressure and temperature
                                         line edits to accept only numeric values. Update to 1.9.3
                        051324:     ADD: Update BVD plots to show raw data as well, fix labels and units in plots. Update ADEV plots to show raw data adev. Update
                                         to 1.9.5
                        051324:     FIX: Rescale raw bv plot after each draw, update to 1.9.5.1
                        062124:     FIX: Clear self.CommentsTextBrowser in clean up, update to 1.9.5.2
                        070124:     ENH: Add ignore first and ignore last line edits and remove Samples used line editrewrote new process thread to allow for correct 
                                         calculations when ignoring last x samples, fix timing diagram, added command line arguments to write debug log, 
                                         select database folder, update to 2.0
                        070524:     ENH: On Save MDSS, the program writes a file '_pyBV.mea' which contains raw and average BV values for the current reversals, 
                                         fix std to std/sqrt(N) for stdA and stdB, update to 2.0
                        071024:     ENH: Add indicators for range shunt and 12 Bit/16 Bit DAC, upgrade to version 2.1
                        071324:     ENH: Add tooltips, add indicator for calibrated mode, update readme, upgrade to version 2.2
                        071424:     ENH: Add more command line options, update readme, add site specific checks, update dependencies, upgrade to version 2.2.1
                        071724:     FIX: h_0 label value now updates when another file is loaded, remove logo
                        020125:     FIX: Fix date search bug for getting environment data, add CCC diagram, add remove outlier checkbox, upgrade to version 2.3
<<<<<<< HEAD
                        021425:     FIX: Fix gui style to be compatible with windows 11, fix issue with R2NomVal for RK/3
                        061325:     ENH: Add warning displays, readback to display if CN is off, fix delete and restore point method for BVD, seperate BV and BVD
                                         tabs, Update ResDataBase.dat, move removed outliers checkbox to bvd tab, upgrade to version 2.4
=======
>>>>>>> d0c9b029c8fe3c268d685ba5d71039651f73f51f
                        """