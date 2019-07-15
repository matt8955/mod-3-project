import pandas as pd
import datetime

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