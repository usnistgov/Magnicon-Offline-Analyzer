
# info
__author__ 		=       "Andrew Geckle & Alireza Panna"
__copyright__ 	=       "This data is publicly available according to the NIST statements of copyright, fair use and licensing; see https://www.nist.gov/director/copyright-fair-use-and-licensing-statements-srd-data-and-software"
__license__ 	=       "NIST"
__maintainer__ 	=       "Alireza Panna"
__email__ 		=       "alireza.panna@nist.gov"
__status__ 		=       "Stable"
__date__        =       "06/2023"
__version__ 	=       "1.9.3"
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
                        """