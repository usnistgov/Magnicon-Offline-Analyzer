
# info
__author__ 		=       "Andrew Geckle & Alireza Panna"
__copyright__ 	=       "This data is publicly available according to the NIST statements of copyright, fair use and licensing; see https://www.nist.gov/director/copyright-fair-use-and-licensing-statements-srd-data-and-software"
__license__ 	=       "NIST"
__maintainer__ 	=       "Alireza Panna"
__email__ 		=       "alireza.panna@nist.gov"
__status__ 		=       "Stable"
__date__        =       "06/2023"
__version__ 	=       "1.6.1"
__ChangeLog__   =       """
                        031224:     FIX: Make R1STPPPM and R2STPPPM linedits editable so user can update predicted value, add requirements.txt
                                    for building project, switch to using allantools for plotting allan deviations since its faster, add 
                                    this file, update to 1.4
                        031324:     ENH: Added autocorrelation (ACF) plots and ability to determine dominant power law noise in data, update
                                    to 1.5
                        031424:     FIX: apply fix for crash when bvd file has no data, mdss file save name changed. write _pyadev.txt, _pypsd.txt and pyCCCRAW.mea files
                        031524      FIX: Add plot labels where necessary, fix more bugs, update to 1.6
                        031624      ENH: Add timing diagram in Help menu, update to 1.6.1
                        """