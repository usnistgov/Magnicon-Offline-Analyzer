README
======

Data analysis software for the powerful Magnicon CCC system.

Installation
------------
Dependencies can be installed using pip:
``pip -r requirements.txt``
Optionally, a spec file is provided to build using pyinstaller::
Tested on windows 10 and 11. This is a windows only program as of now.


Usage
-----
If you have python installed on your system then you can call:
```
pip -r requirements.txt
python Magnicon-Offline-Analyzer.py
```
Optionally to show the help menu:
``python Magnicon-Offline-Analyzer.py -h``

If you are running the exe and want to see the help menu\
Enter this in the cmd window
``Magnicon-Offline-Analyzer.exe -h | more``
This will launch the splash screen and show the help menu once the program is finished \ loading. For now there is no way to not show the splash screen but I am trying to fix \
this for future releases. Supported options are shown below
```
Configure Magnicon-Offline-Analyzer

options:
  -h, --help            show this help message and exit
  -db DB_PATH, --db_path DB_PATH
                        Specify resistor database directory
  -l LOG_PATH, --log_path LOG_PATH
                        Specify log directory
  -d, --debug           Debugging mode
  -s SITE, --site SITE  Site where this program is used
  -c SPECIFIC_GRAVITY, --specific_gravity SPECIFIC_GRAVITY
                        Specific gravity of oil for oil type resistors

A utility to interact with the analysis software for Magnicon CCC systems

```

DB_PATH is the path to the resistor database directory\
In debugging mode, debug logs are saved to the log file specfied by the LOG_PATH

Contact
-------
To report bugs or request features, please contact:\
alireza.panna@nist.gov

Acknowledgements
----------------
This package benefits greatly from a number of packages but specially the two of them listed here:
1. [allantools](https://github.com/aewallin/allantools)
2. [lcapy](https://github.com/mph-/lcapy)