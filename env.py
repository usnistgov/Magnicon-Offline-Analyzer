from numpy import asarray, float64, nan
from pandas import read_csv, to_datetime, concat
from os import sep, scandir
from datetime import datetime

EPOCH = 2082844800
class env:
    def __init__(self, filepath, start_datetime, end_datetime):
        
        self.filepath = filepath
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        # print('1. ', self.start_datetime, self.end_datetime)
        self.start_time = datetime.strptime(self.start_datetime, '%m/%d/%Y %I:%M:%S %p')
        self.end_time = datetime.strptime(self.end_datetime, '%m/%d/%Y %I:%M:%S %p')
        # print('2. ', self.start_time, self.end_time)
        self.start_date = start_datetime.split(' ')[0]
        self.start_date = datetime.strptime(self.start_date, '%m/%d/%Y')
        # print('2.5 ', self.start_date)
        self.start_date_fin = self.start_date.strftime('%Y%m%d')
        self.end_date = end_datetime.split(' ')[0]
        self.end_date = datetime.strptime(self.end_date, '%m/%d/%Y')
        self.end_date_fin = self.end_date.strftime('%Y%m%d')
        # print('3. ', self.start_date_fin, self.end_date_fin)
        x = datetime.timestamp(self.start_time)
        y = datetime.timestamp(self.end_time)
        # to convert from unix (posix) timestamp to labview timestamp...
        # z = (datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc) - datetime(1904, 1, 1, 0, 0, 0, tzinfo=timezone.utc)).total_seconds()
        self.start_timestamp = x # referenced to posix timestamp
        self.end_timestamp = y # referenced to posix timestamp
        self.mydata = []

    def _read_helper(self, filename, ):
        """Helper function for get_data()

        Parameters
        ----------
        filename : str
            name of csv file to read
        Returns
        -------
        mydata : list
            data in the csv file
        """
        try:
            mydata = []
            mydata.append(read_csv(filename, sep='\t', dtype={0:"float64", 1:"float64", 2:"float64"},\
                                   on_bad_lines='skip', na_filter=True, index_col=False, memory_map=True, \
                                   engine='c', names=['TS','T','P'], lineterminator='\n'))
            return mydata
        except Exception as e:
            print('Error in file: ', filename)
            print(e)

    def _get_data(self):
        try:
            for filename in scandir(self.filepath):
                self.filename = filename.name
                # print(self.filename)
                # print ((filename.name.split('_')[-1]).split('.')[0], self.start_date_fin, self.end_date_fin)
                if filename.name != '' and ((filename.name.split('_')[-1]).split('.')[0] == self.start_date_fin \
                   or (filename.name.split('_')[-1]).split('.')[0] == self.end_date_fin):
                    self.mydata.append(self._read_helper(self.filepath + sep + filename.name))  
            for i in self.mydata:
                self.df = concat(i,ignore_index = True )
            self.df['TS'] = self.df['TS'] - EPOCH # labview timestamp to posix timestamp
            self.df.insert(0, "Date", to_datetime(self.df['TS'], utc=True, unit='s'))
            self.df['Date'] = self.df['Date'].dt.tz_convert('America/New_York')
            # to convert to eastern time use below
            self.df.set_index('Date', inplace=True)
            # print(self.df)
        except Exception as e:
            print(e)
            pass
    
    def calc_average(self):
        """ Calculates the mean of the sample temperature data
            within the specified interval
        Returns
        -------
        None.
        """
        self._get_data()
        new_df = None
        try:
            # print(self.start_timestamp, self.df['TS'])
            new_df = self.df[(self.df['TS'] >= self.start_timestamp) & (self.df['TS'] <= self.end_timestamp)]
            # print(new_df.head(3), new_df.tail(3))
            new_df.astype({'TS': 'float64'}).dtypes
            # print(new_df_tempCtrl.describe())
            # sampleT_mean = new_df_tempCtrl['Sample temp'].mean(skipna=True, numeric_only=True)
            T_mean = round(asarray(new_df['T'], dtype=float64).mean(), 6)
            P_mean = round(asarray(new_df['P'], dtype=float64).mean(), 6)
            return(T_mean, P_mean*1e3)
        except Exception as e:
            print(e)
            return(nan, nan)
            pass

if __name__ == "__main__":
    debug = False
    if debug == True:
        obj = env(r'C:\Environment\Room-E014', '4/5/2024 06:14:18 PM', '4/5/2024 06:20:18 PM')
        obj.get_data()
        obj.calc_average()