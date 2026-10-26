import logging
import os
from time import time
from datetime import datetime as dt
from pytz import utc

logger = logging.getLogger(__name__)

EPOCH = 2082844800 # seconds from the LabVIEW epoch (1/1/1904) to the Unix epoch (1/1/1970)

# MySQL resistor database: table resistors_database, made from the ResDataBase*.dat files by resdb_import.py
MYSQL_DEFAULTS = {'host': 'localhost', 'port': 3306, 'user': 'root', 'database': 'resdb'}
MYSQL_TIMEOUT  = 2   # s to wait for the connection (mysql-connector 8.0.21 waits about twice as long)
MYSQL_RETRY    = 300 # s before a connection that failed is tried again, so every file load does not wait for it
MYSQL_FIELDS   = ('NomVal', 'CalVal', 'Alpha', 'Beta', 'PCR', 'Drift', 'StdTemp')
MYSQL_COLUMNS  = 'SELECT sn, cal_date, nom_val, cal_val, alpha, beta, pcr, drift, std_temp FROM resistors_database '
# the current values of every resistor
MYSQL_QUERY    = MYSQL_COLUMNS + 'WHERE valid_to IS NULL ORDER BY valid_from'
# the values of every resistor in effect at a time: valid_from <= time < valid_to (NULL: still current). The
# 'initial' values (as found in the oldest .dat file) are also used before that file, since when they were set is
# not known. A resistor 'added' later was not in the database before it was added
MYSQL_QUERY_AT = MYSQL_COLUMNS + "WHERE (valid_from <= %s OR changed = 'initial') " + \
                 'AND (valid_to > %s OR valid_to IS NULL) ORDER BY valid_from'
mysql_failed_at = 0.0 # time of the last failed connection
mysql_error     = ''  # why it failed

class ResData():
    def __init__(self, bp: str = None):
        self.ResDict = {}
        self.source  = '' # where the values come from
        if bp is None: # filled by from_rows or from_mysql
            return
        try:
            self.datFile = f'{bp}\\ResDataBase.dat'
            self.source  = self.datFile
            # Empty arrays to store data from ResDataBase.dat
            self.ResDict = {}
            # Open .dat file for reading and close it when done
            with open (self.datFile, "r") as f:
                # Parse each line of the .dat file and append the date into the data arrays
                for line in f.readlines():
                    # Stores the Cal Val and converts LabView based timestamp (1,1,1904) to Unix-based timestamp (1,1,1970) making sure everything is in UTC
                    if line.startswith('CalDate'):
                        # Creates a temporary variable to store the current Cal Val
                        CalDate = float(line.split('=')[-1].rstrip(' \n'))
                        # Convert to a Unix-based timestamp (subtracting 66 calendar years is off by up to a day due to leap years)
                        CorrCalDate = CalDate - EPOCH
                    elif line.startswith('SN'):
                        temp = line.split('=')[-1].rstrip(' "\n')
                        SN   = temp.lstrip(' "')
                        self.ResDict[SN] = {}
                        self.ResDict[SN]['CalDate'] = CalDate
                        self.ResDict[SN]['CorrCalDate'] = CorrCalDate
                    elif line.startswith('NomVal'):
                        self.ResDict[SN]['NomVal'] = float(line.split('=')[-1].rstrip(' \n'))
                    elif line.startswith('CalVal'):
                        self.ResDict[SN]['CalVal'] = float(line.split('=')[-1].rstrip(' \n'))
                    elif line.startswith('Alpha'):
                        self.ResDict[SN]['Alpha'] = float(line.split('=')[-1].rstrip(' \n'))
                    elif line.startswith('Beta'):
                        self.ResDict[SN]['Beta'] = float(line.split('=')[-1].rstrip(' \n'))
                    elif line.startswith('PCR'):
                        self.ResDict[SN]['PCR'] = float(line.split('=')[-1].rstrip(' \n'))
                    elif line.startswith('Drift'):
                        self.ResDict[SN]['Drift'] = float(line.split('=')[-1].rstrip(' \n'))
                    elif line.startswith('StdTemp'):
                        self.ResDict[SN]['StdTemp'] = float(line.split('=')[-1].rstrip(' \n'))
        except Exception as e:
            print(e)
            pass

    @classmethod
    def from_rows(cls, rows) -> 'ResData':
        """ResData from (sn, cal_date, nom_val, cal_val, alpha, beta, pcr, drift, std_temp) rows of the
           resistors_database table. resdb_import.py stores the LabVIEW CalDate as a local time without a time zone
           (NULL for CalDate = 0), so cal_date is converted back with the local time zone of this computer
        """
        R = cls()
        for sn, cal_date, *values in rows:
            if isinstance(sn, (bytes, bytearray)): # the sn column is binary collated
                sn = sn.decode('utf-8')
            CorrCalDate = -EPOCH if cal_date is None else cal_date.timestamp() # Unix time, as for the .dat file
            R.ResDict[sn] = {'CalDate': CorrCalDate + EPOCH, 'CorrCalDate': CorrCalDate}
            for key, value in zip(MYSQL_FIELDS, values):
                if value is not None: # a value missing in the .dat file is missing here too
                    R.ResDict[sn][key] = float(value)
        return R

    @classmethod
    def from_mysql(cls, host: str = MYSQL_DEFAULTS['host'], port: int = MYSQL_DEFAULTS['port'], \
                   user: str = MYSQL_DEFAULTS['user'], database: str = MYSQL_DEFAULTS['database'], \
                   password: str = None, when: dt = None) -> 'ResData':
        """The values of every resistor from the MySQL table resistors_database that were in effect at when (a local
           time without a time zone, like valid_from and valid_to), the current values when it is None. The
           password is read from the MYSQL_PWD environment variable when it is not given. Raises an exception when
           the database cannot be reached or read
        """
        import mysql.connector # only needed for the MySQL database
        if password is None:
            password = os.environ.get('MYSQL_PWD', '')
        connection = mysql.connector.connect(host=host, port=port, user=user, password=password, database=database, \
                                             connection_timeout=MYSQL_TIMEOUT, use_pure=True)
        try:
            cursor = connection.cursor()
            if when is None:
                cursor.execute(MYSQL_QUERY)
            else:
                cursor.execute(MYSQL_QUERY_AT, (when, when))
            rows = cursor.fetchall()
        finally:
            connection.close()
        if not rows:
            raise ValueError('resistors_database has no values' + ('' if when is None else f' for {when}'))
        R = cls.from_rows(rows)
        R.source = f'MySQL {database}.resistors_database on {host}, ' + \
                   ('current values' if when is None else f'values in effect on {when:%m/%d/%Y %I:%M:%S %p}')
        return R

    # Returns the predicted resistor value from the input SN and datetime in mm/dd/yyyy format
    def predictedValueDate(self, mySN: str, myDate: str) -> float:
        # Converts the input datetime into a timestamp
        temp = dt.strptime(myDate, "%m/%d/%Y")
        myTimeStamp = dt.timestamp(dt(temp.year, temp.month, temp.day, tzinfo=utc))
        # Return the predicted value if input SN is found within the database
        if mySN in self.ResDict:
            return (self.ResDict[mySN]['Drift']*((myTimeStamp - self.ResDict[mySN]['CorrCalDate'])/(365.25*24*60*60)) + self.ResDict[mySN]['CalVal'])
        # Return None if the input SN is not found within the database
        return None
    # Returns the predicted resistor value from the input SN and Unix timestamp
    def predictedValueUnix(self, mySN: str, myUnixTime: float) -> float:
        # Return the predicted value if input SN is found within the database
        if mySN in self.ResDict:
            return (self.ResDict[mySN]['Drift']*((myUnixTime - self.ResDict[mySN]['CorrCalDate'])/(365.25*24*60*60)) + self.ResDict[mySN]['CalVal'])
        # Return None if the input SN is not found within the database
        return None

def load_mysql(config: dict = None, when: dt = None) -> ResData:
    """The resistor database from MySQL (config: host, port, user, password, database, see MYSQL_DEFAULTS) with the
       values in effect at when (the current values when it is None), or None when it cannot be read. After a
       failure it is not tried again for MYSQL_RETRY s, mysql_error says why it failed
    """
    global mysql_failed_at, mysql_error
    if time() - mysql_failed_at < MYSQL_RETRY:
        return None
    settings = dict(MYSQL_DEFAULTS, **(config or {}))
    try:
        R = ResData.from_mysql(**settings, when=when)
        mysql_error = ''
        return R
    except Exception as e:
        mysql_failed_at = time()
        mysql_error = f"{settings['database']} on {settings['host']}: {type(e).__name__}: {e}"
        logger.warning('MySQL resistor database cannot be read, ' + mysql_error)
        return None

if __name__ == '__main__':
    print ("I am main")