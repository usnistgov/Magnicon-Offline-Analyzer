from datetime import timedelta, datetime as dt
from dateutil.relativedelta import relativedelta
from pytz import utc

class ResData():
    def __init__(self, bp):
        self.datFile = f'{bp}\ResDataBase.dat'
        
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
                    # Subtract 66 years to get to Unix based date objects
                    UnixDateObj = dt.fromtimestamp(CalDate, tz=utc) - relativedelta(years=66)
                    # Convert datetime into corrected Unix-based timestamp
                    CorrCalDate = (UnixDateObj - dt(1970,1,1,0,0,tzinfo=utc)) / timedelta(seconds=1)
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
    
    
# Main
if __name__ == '__main__':
    pass