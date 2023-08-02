from os import sep
from datetime import timedelta, datetime as dt
from dateutil.relativedelta import relativedelta
from pytz import utc

class ResData():
    def __init__(self, bp):
        self.files = bp + sep + 'ResDataBase.dat'
        
        # Empty arrays to store data from ResDataBase.dat
        self.calDate = []
        self.SN = []
        self.nomVal = []
        self.calVal = []
        self.alpha = []
        self.beta = []
        self.pcr = []
        self.drift = []
        self.stdTemp = []
        self.corrCalDate = []

        # Open .dat file for reading and close it when done
        with open (self.files, "r") as f:
            # Parse each line of the .dat file and append the date into the data arrays
            for line in f.readlines():
                # Stores the Cal Val and converts LabView based timestamp (1,1,1904) to Unix-based timestamp (1,1,1970) making sure everything is in UTC
                if line.startswith('CalDate'):
                    # Creates a temporary variable to store the current Cal Val
                    temp = float(line.split('=')[-1].rstrip(' \n'))
                    self.calDate.append(temp)
                    # Subtract 66 years to get to Unix based date objects
                    temp = dt.fromtimestamp(temp, tz=utc) - relativedelta(years=66)
                    # Convert datetime into corrected Unix-based timestamp
                    self.corrCalDate.append((temp - dt(1970,1,1,0,0,tzinfo=utc)) / timedelta(seconds=1))
                if line.startswith('SN'):
                    sn = line.split('=')[-1].rstrip(' "\n')
                    self.SN.append((sn.lstrip(' "')))
                if line.startswith('NomVal'):
                    self.nomVal.append(float(line.split('=')[-1].rstrip(' \n')))
                if line.startswith('CalVal'):
                    self.calVal.append(float(line.split('=')[-1].rstrip(' \n')))
                if line.startswith('Alpha'):
                    self.alpha.append(float(line.split('=')[-1].rstrip(' \n')))
                if line.startswith('Beta'):
                    self.beta.append(float(line.split('=')[-1].rstrip(' \n')))
                if line.startswith('PCR'):
                    self.pcr.append(float(line.split('=')[-1].rstrip(' \n')))
                if line.startswith('Drift'):
                    self.drift.append(float(line.split('=')[-1].rstrip(' \n')))
                if line.startswith('StdTemp'):
                    self.stdTemp.append(float(line.split('=')[-1].rstrip(' \n')))

    # Returns the predicted resistor value from the input SN and datetime in mm/dd/yyyy format
    def predictedValueDate(self, mySN, myDate):
        # Converts the input datetime into a timestamp
        temp = dt.strptime(myDate, "%m/%d/%Y")
        myTimeStamp = dt.timestamp(dt(temp.year, temp.month, temp.day, tzinfo=utc))
        # Searches the database for a matching SN
        for index, SN  in enumerate(self.SN):
            # Return the predicted value if input SN is found within the database
            if SN == mySN:
                return (self.drift[index]*((myTimeStamp - self.corrCalDate[index])/(365.25*24*60*60)) + self.calVal[index])
        # Return 0 if the input SN is not found within the database
        return (0)
            
    # Returns the predicted resistor value from the input SN and Unix timestamp
    def predictedValueUnix(self, mySN, myUnixTime):
        # Searches the database for a matching SN
        for index, SN  in enumerate(self.SN):
            # Return the predicted value if input SN is found within the database
            if SN == mySN:
                return (self.drift[index]*((myUnixTime - self.corrCalDate[index])/(365.25*24*60*60)) + self.calVal[index])
        # Return 0 if the input SN is not found within the database
        return (0)
    
    # Returns the index of the database for the input SN
    def getSNindex(self, mySN):
        for index, SN in enumerate(self.SN):
            if SN == mySN:
                return (index)
        # Returns 0 if the SN is not in the database
        return (0)

# Main
if __name__ == '__main__':
    pass