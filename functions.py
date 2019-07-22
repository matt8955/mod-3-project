import pandas as pd
import requests
import json
import time

class scrape():
    symbols = []
    frames = []
    fails = []
    success = []
    frame_list = []
    merged_df = pd.DataFrame()

    def __init__(self, symbol):
        self.symbol = symbol.strip()
        scrape.symbols.append(self.symbol)
        self.df = self.scrape_symbol()
        self.df = self.reformat_columns()
        self.df = self.typecast_df()
        self.df = self.rearrange_cols()
        self.df = self.date_to_column()
        self.close_df = self.closing_price()
        scrape.frame_list.append(self.close_df)

    def scrape_symbol(self):
        '''takes in a list of stock symbols and scrapes their interday data
        returns a ist of dataframes scraped Dataframes'''
        print(f'scraping{self.symbol}')
        key = 'HPC1NZDRG2SE3EEH'
        req = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={self.symbol}&outputsize=full&apikey={key}')
        try:
            if req.status_code == 200:
                data = json.loads(req.text)
                df = pd.DataFrame(data['Time Series (Daily)']).transpose()
                df['symbol'] = self.symbol
                df.columns = list(map(str.lower, df.columns))
                scrape.success.append(self.symbol)
                time.sleep(20)
                return df
            else:
                scrape.fails.append(self.symbol)
        except:
            scrape.fails.append(self.symbol)

    def reformat_columns(self):
        '''takes in scraped df and returns a df with
        reformatted columns'''
        new_names = []
        for col in self.df.columns[0:8]:
            self.df[col] = self.df[col].astype(float) #change type to float
            new_name = col.split()[1:]
            new_names.append(' '.join(new_name))
        new_names.append(self.df.columns[8])
        self.df.columns = new_names #rename cols
        return self.df

    def typecast_df(self):
        '''takes in scraped df and changes the numerical
        columns from object into a float'''
        for col in self.df.columns[0:8]:
            self.df[col] = self.df[col].astype(float)
        return self.df

    def rearrange_cols(self):
        '''rearranges columns in df for proper formatting'''
        self.df = self.df[[self.df.columns[8]] + list(self.df.columns[0:8])]
        return self.df

    def date_to_column(self):
        '''makes the pops date off the index and make it a column'''
        self.df.reset_index(level=0, inplace=True) #pop off index
        self.df.columns = ['date'] + list(self.df.columns[1:]) #change name of index col to date
        return self.df

    def closing_price(self):
        '''augments the scraped dataframe to have date symbol and price'''
        df_close = self.df[['date','close']]
        df_close.columns = ['date', self.symbol]
        return df_close

    @classmethod
    def merge_frames(cls):
        df = scrape.frame_list[0]
        for frame in scrape.frame_list[1:]:
            df = df.merge(frame, on='date')
        scrape.merged_df = df

    @classmethod
    def add_to_db(cls, table_name, engine):
        '''adds frame to database'''
        scrape.merged_df.to_sql(table_name, con=engine)



def transform_to_august_returns(df):
    '''takes in a dataframe with interday stock prices and calculates the percentage return for
     year till july for each stock'''
    df = df.copy()
    first_day_jan = ['2014-01-03', '2015-01-02', '2016-01-04', '2017-01-03', '2018-01-02', '2019-01-02']
    first_day_jul = ['2014-07-01', '2015-07-01', '2016-07-01', '2017-07-03', '2018-07-02', '2019-07-01']

    august_returns_df = pd.DataFrame()
    for i in range(6):
        august_returns_df[f'201{4+i}'] = (df.loc[first_day_jul[i]] - df.loc[first_day_jan[i]]) / df.loc[first_day_jan[i]]
    return august_returns_df
