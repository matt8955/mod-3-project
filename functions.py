import pandas as pd
import datetime
import tqdm
import requests
import json
import time

def scrape_symbols(symbols):
    '''takes in a list of stock symbols and scrapes their interday data
    returns a tuple with a list of dataframes with each stocks data, a list of 
    sucessful tickers, a list of failed tickers'''
    key = 'HPC1NZDRG2SE3EEH'
    frame_list = []
    success = []
    fails = []
    for symbol in tqdm.tqdm(symbols[0:1]):
        symbol = symbol.strip()
        req = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={key}')

        try:
            if req.status_code == 200:
                data = json.loads(req.text)
                df = df = pd.DataFrame(data['Time Series (Daily)']).transpose()
                df['symbol'] = symbol
                df.columns = map(str.lower, df.columns)
                frame_list.append(df.copy())
                success.append(symbol)
                time.sleep(20)
            else:
                fails.append(symbol)

        except:
            fails.append(symbol)
    return (frame_list, success, fails)
    

def reformat_columns(df):
    '''takes in scraped df and returns a df with
    reformatted columns'''
    df = df.copy()
    new_names = []
    for col in df.columns[0:8]:
        df[col] = df[col].astype(float) #change type to float
        new_name = col.split()[1:]
        new_names.append(' '.join(new_name))
    new_names.append(df.columns[8])
    df.columns = new_names #rename cols
    return df

def typecast_df(df):
    '''takes in scraped df and changes the numerical 
    columns from object into a float'''
    df = df.copy()
    for col in df.columns[0:8]:
        df[col] = df[col].astype(float)
    return df

def rearrange_cols(df):
    df = df.copy()
    df = df[[df.columns[8]] + list(df.columns[0:8])]
    return df

def date_to_column(df):
    df = df.copy()
    df.reset_index(level=0, inplace=True) #pop off index
    df.columns = ['date'] + list(df.columns[1:]) #change name of index col to date
    return df

def clean_frames(df_list):
    '''takes in list of dataframes and cleans them by chnging the types and moving
    around indicies'''
    df_list = df_list.copy()
    cleaned = []
    for df in df_list:
        df = reformat_columns(df)
        df = typecast_df(df)
        df = rearrange_cols(df)
        df = date_to_column(df)
        cleaned.append(df)
    return cleaned
        
def reshape_df_for_sql(frame_list, column):
    '''takes a list of the base dataframes and subsets them and then joins 
    to the correct format to create a sql table'''
    pass

def join_df(framelist):
    pass 

def transform_to_august_returns(df):
    df = df.copy()
    first_day_jan = ['2014-01-03', '2015-01-02', '2016-01-04', '2017-01-03', '2018-01-02', '2019-01-02']
    first_day_jul = ['2014-07-01', '2015-07-01', '2016-07-01', '2017-07-03', '2018-07-02', '2019-07-01']

    august_returns_df = pd.DataFrame()
    for i in range(6):
        august_returns_df[f'201{4+i}'] = 1 - (df.loc[first_day_jul[i]] / df.loc[first_day_jan[i]])
    return august_returns_df

