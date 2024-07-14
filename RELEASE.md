# RELEASE

## 07/14/2024   Version 2.2.1
  * Added command line options to enter custom value for specific gravity of oil
  * Added command line option for future site specific configuration
  * Update About window
  * Update external dependencies

## 07/13/2024   Version 2.2
  * Fix tooltips
  * Add calibrated mode indicator
  * Fix location of range shunt and 12 bit DAC indicators in the ui
  * Update README.md

## 07/10/2024   Version 2.1
  * Add indicators for range shunt and 12 Bit/16 Bit DAC

## 07/05/2024   Version 2.0
  * Add ignore first and ignore last line edits and remove Samples used line edit
  * Rewrote new process thread to allow for correct calculations when ignoring last x samples
  * Fix timing diagram
  * Added command line arguments to write debug log, select database folder
  * On Save MDSS the program writes a file '_pyBV.mea' which contains raw and average BV values for the current reversals
  * fix std to std/sqrt(N) for stdA and stdB

## 06/21/2024   Version 1.9.5.2
  * Rescale raw bv plot after each draw
  * Clear self.CommentsTextBrowser in clean up

## 05/13/2024   Version 1.9.5
  * Update BVD plots to show raw data as well
  * Fix labels and units in plots
  * Update ADEV plots to show raw data adev

## 04/29/2024   Version 1.9.3
  * mdss files writes correct R1STP and R2STP prediction values if user changes them to be custom values
  * new custom icon for the project
  * Add ratio stdMean line edit
  * Add ratio value to comment 
  * Set pressure and temperature line edits to accept only numeric values

## 04/13/2024   Version 1.9.1
  * Fix filename for .mea file
  * Fix pressure readout

## 04/11/2024   Version 1.9
  * Add show/hide tooltip submenu under help menu
  * Fix timing diagram equation

## 04/10/2024   Version 1.8
  * Remove unused imports
  * Add more precision digits to temperature line edits
  * Fix issues with checks and add some tooltips

## 04/09/2024   Version 1.7
  * Add folder paths for temperature and calculate the average temperatures for R1 and R2 automatically
  * Fix color issue with MDSS Save button

## 03/29/2024   Version 1.6.4
  * Fix crash when loading incomplete bvd files

## 03/21/2024   Version 1.6.3
  * Add start and end time line edits
  * fix I+ and I- labels in plot

## 03/14/2024   Version 1.6
  * Apply fix for crash when bvd file has no data, mdss file save name changed 
  * write _pyadev.txt, _pypsd.txt and pyCCCRAW.mea files
  * Add plot labels where necessary

## 03/13/2024   Version 1.5
  * Added autocorrelation (ACF) plots
  * ability to determine dominant power law noise in data via lag 1 autocorrelation                           

## 03/12/2024   Version 1.4
  * Make R1STPPPM and R2STPPPM linedits editable so user can update predicted value
  * Add requirements.txt for building project
