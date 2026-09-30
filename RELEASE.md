# RELEASE

## 09/29/2026 Version 3.1.0
### New
  * File > Batch Process... (Ctrl+B) processes and saves several data files at a time. The settings (Standard R,
    SQUID feedin polarity and arm, electronics, probe, oil depths, environment paths, Remove Outliers and Detrend)
    are used for every file. With QHR Char checked the files are saved as QHR Process with the typed QHR values,
    otherwise as Magnicon CCC Process. The ignored samples, Delta(I2R2) and STP predictions are those of each file
  * Each file gets the same pymdss, _pyCCCRAW.mea and _pyBV.mea files as MDSS Save. The ADEV and PSD are not
    calculated, so no _pyadev/_pypsd files are written
  * A summary of the results (mean, std dev, std mean, R Mean Chk, R Mean - Chk, C1-C2, ratio, BVD, N, temperatures,
    pressures, STP predictions, settings, warnings and errors) is written to one pyBatch_<date>_<time>.csv file per
    batch, next to the data files. Files that cannot be processed are listed and the batch goes on, Cancel stops
    after the current file

### Fixes
  * The total pressures are those of the loaded file. Without an environment path they kept the value of the
    previous file, or of a pressure typed in for it, while the pressure box showed 101325 Pa. This can change the
    results if a pressure was typed in before another file was opened
  * Clicking Standard R after an invalid file was loaded no longer gives an error
  * update to 3.1.0

### AI use
  * Made with the help of an AI coding assistant (Claude Opus 5.5 by Anthropic, used through Claude Code) at the
    direction of the maintainer. Checked with the sample runs: the files saved by Batch Process are identical to the
    ones saved with MDSS Save (default settings, QHR Char, Remove Outliers with Detrend, R2 as the standard), and the
    results with the default settings are unchanged

## 09/29/2026 Version 3.0.1
  * The R1/R2 plot shows the mean with overlapping quadratic drift removal (Detrend: Overlap) as a dashed line next
    to the mean of the selected Detrend setting. Both means are listed in the legend, rounded to 3 decimals. With
    Detrend: Overlap selected the two are the same and only one line is shown
  * The R Mean - R Mean Chk box has its label, R Mean - Chk [ppb] (the old label was hidden under the box). The
    results column is re-spaced to fit it
  * Faster drift removal for long runs (2880 cycles: Overlap 2.9 s -> 0.8 s, No-Overlap 1.6 s -> 0.6 s), with the
    same results
  * AI use: made with the help of an AI coding assistant (Claude Opus 5.5 by Anthropic, used through Claude Code) at
    the direction of the maintainer. Checked with the sample runs (results unchanged) and by comparing the new mean
    line with the result of Detrend: Overlap
  * update to 3.0.1

## 09/27/2026 Version 3.0.0
### Results that can change compared to 2.5.1
  * Detrend: the quadratic fit over each cycle also absorbed about 70% of the current reversal step, so Detrend
    reported about 30% of the true BVD (the resistance was off by several nOhm/Ohm). The drift is now fitted together
    with the step, in time order, over two cycles, and only the drift is subtracted. No-Overlap uses windows that
    follow each other, Overlap starts a window at every cycle like the overlapping Allan deviation
  * Remove Outliers and Delete/Restore Last leave out the same cycles from every per-cycle list. Before, with Remove
    Outliers on, C1/C2 and their std devs were computed from shifted cycles, and Restore Last put back the wrong C1/C2
    after more than one delete. The delete list and the BVD plot use the original cycle numbers
  * Resistor database calibration dates are converted with the exact LabVIEW epoch offset. The old conversion put
    71 of the 359 calibration dates in data/ResDataBase.dat one day late, which changes the STP predictions of those
    resistors by up to 0.3 ppm (typically about 5 nOhm/Ohm)
  * Environment (temperature/pressure) averages use the files for every day an overnight or multi-day run spans.
    Previously only one day's file was used
  * Deleted points and typed-in values (ignored samples, Delta(I2R2), STP predictions) are kept when other settings
    change. They are cleared when a file is loaded or replotted. Before, changing e.g. a temperature silently reverted
    them, and the Ignored First/Last, Delay and Meas boxes could show other values than the ones used for the results

### New
  * Carrier density n [cm^-2] line edit for QHR Char. The value is written to the pymdss file as the entry before
    StandRes, so QHR Process lines have one more field
  * Rename Sample T [K] to Samp. T [K] and re-space the QHR widgets so they fit in one row
  * The CCC diagram is drawn with schemdraw instead of lcapy, so LaTeX/TeX Live is no longer needed or bundled with
    the program. lcapy and the packages only it needed are removed from requirements.txt

### Fixes
  * Crashes: comma in a pressure field, unreachable NIST network share (now falls back to the local
    ResDataBase.dat with a warning), runs with a single BVD point and a first file with fewer than 4 cycles.
    Numeric fields no longer accept group separators
  * Unhandled errors are logged and shown in a dialog instead of closing the program, and a failed save no longer
    leaves a partial pymdss file
  * The warning dialog lists each warning once (it repeated them after every update), and closing the main window
    quits the program even when the About or Timing Diagram window is open
  * Fix the .cfg pattern for R_K/118 resistors ('2.817' -> '2.187') and remove code that had no effect
  * Add .gitignore, remove invalid escape sequences, update to 3.0.0

### AI use
  * The changes in this release were made with the help of an AI coding assistant (Claude Opus 5.5 by Anthropic,
    used through Claude Code) at the direction of the maintainer. They were checked with the sample runs in this
    repository, which give the same results as before with the default settings, and with simulated data for the
    BVD, Remove Outliers, Delete/Restore Last and Detrend calculations

## 06/12/2026 Version 2.5.1
  * add analysis version in the comment string, add uncorrected unknown value in ppm in comment string,
    fix ratio value updates in comment string, update to 2.5.1

## 08/01/2025 Version 2.5
  * Display mean value of R1 or R2 in plot as a horizontal line
  * Linear fit the BVD data and display slope in nV/sec
  * TODO: Perform quadratic correction of BV data to get BVD.

## 06/20/2025 Version 2.4.1
  * If screen voltage is off, then the program shows a warning. Guard voltage is set to 0 in pymdss.txt file if screen 
    voltage is off
  * Seperated BVD and R plots so its easy to view
  * Added QHR Char checkbox to save QHR Process in pymdss file

## 06/13/2025 Version 2.4
  * Add warning displays if CN output is off or cal mode is off or 16 bit daq correction is not 0
  * Add readback to display if compensation (CN) output is on or off
  * Seperate bridge voltage (BV) and bridge voltage difference (BVD) tabs. Show raw bridge voltages as well
  * Re-orient count combo box in BVD tab so it goes in descending order making it easier to delete points incase of SQUID unlock
  * Fix plotCountComboBox issue when deleting points from BVD plot
  * Moved Remove Outliers checkbox to BVD tab
  * Update ResDataBase.dat to latest

## 02/14/2025 Version 2.3.1
  * Fix issue with R2NomVal for RK/3 value
  * Fix gui style to be compatible with windows 11

## 02/01/2025 Version 2.3
  * Fix date search bug for getting environment data
  * Add CCC diagram, requires pdftex to run
  * Add remove outlier checkbox. When selected, removes BVDs that are > +/-3 sigma from the mean
  
## 07/17/2024   Version 2.2.2
  * Remove logo
  * Fix issue where h_o label value in PSD of BVD plot was not updating 

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
