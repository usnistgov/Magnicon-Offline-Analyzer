README
======

Data analysis software for the powerful Magnicon CCC system.

Installation
------------

Dependencies can be installed using pip:
``pip -r requirements.txt``
Optionally, a spec file is provided to build using pyinstaller::
Tested on windows 10, 11.

Usage
-----
If you have python installed on your system then you can call:\
```pip -r requirements.txt
python Magnicon-Offline-Analyzer.py
```

Magnicon-Offline-Analyzer.exe -h | more

```
Configure Magnicon-Offline-Analyzer

options:
  -h, --help            show this help message and exit
  -db DB_PATH, --db_path DB_PATH
                        Specify resistor database directory
  -l LOG_PATH, --log_path LOG_PATH
                        Specify log directory
  -d, --debug           Debugging mode

A utility to interact with the analysis software for Magnicon CCC systems

```

DB_PATH is the path to the resistor database directory\
In debugging mode, debug logs are saved to the log file specfied by the LOG_PATH

Contact
-------
To report bugs or request features, please contact:\
alireza.panna@nist.gov