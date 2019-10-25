from Clean import Clean
import os
import re
import unicodedata
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup 
from lxml import html
from tqdm import tqdm
from inscriptis import get_text
import urllib.request
import copy
from textblob import TextBlob
import pickle
from sklearn.feature_extraction.text import CountVectorizer
import workdays
from datetime import datetime
from datetime import timedelta
from iexfinance.stocks import get_historical_data
import seaborn as sns
import matplotlib.pyplot as plt



def get_latest_yoy_metrics(tickers, k_or_q='k'):
    """Automatically evaluate the change in YoY cosine similarity and sentiment for a company's latest SEC filing
    
    Keywords:
    tickers -- a list of stock tickers
    k_or_q -- evaluate most recent yearly report (k) or quarterly report {q}"""
    
    scores = {}
    problems =[]
    for ticker in tqdm(tickers):
        if k_or_q=='k':
            rss = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + str(ticker) +'&type=10-k%25&dateb=&owner=exclude&start=0&count=40&output=atom'
        else:
            rss = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + str(ticker) +'&type=10-q%25&dateb=&owner=exclude&start=0&count=40&output=atom'
        #obtain SEC edgar index page links
        page = requests.get(rss)
        filing_dates = [i.string for i in BeautifulSoup(page.content, 'html.parser').find_all('filing-date')]
        indices = [i.string for i in BeautifulSoup(page.content, 'html.parser').find_all('filing-href')]
        if (len(indices)>=2) & (k_or_q=='k'):
            indices = indices[:2]
            filing_dates=filing_dates[:2]
        elif (len(indices)>=4) & (k_or_q=='q'):
            start = filing_dates[0]
            correct_year = [i for i in filing_dates if int(start.split('-')[0]) - int(i.split('-')[0]) == 1]
            month_diffs = [abs(int(start.split('-')[1]) - int(i.split('-')[1])) for i in correct_year]
            correct_date_index = correct_year[month_diffs.index(min(month_diffs))]
            correct_report = filing_dates.index(correct_date_index)
            indices = [indices[0],indices[correct_report]]
            filing_dates = [filing_dates[0],filing_dates[correct_report]]
        else:
            problems.append(ticker)
            continue
        #obtain links to relevant reports
        report_links = []
        for i in range(len(indices)):
            page = requests.get(indices[i])
            index_links = [j.get('href') for j in BeautifulSoup(page.content,'html.parser').find_all('a')]
            index_links = [j for j in index_links if ('/Archives/edgar/data' in j) & (j[-4:]=='.htm')]
            if len(index_links)>0:
                link = 'https://www.sec.gov' + index_links[0]
                report_links.append(link)
        #identify whether report has recently changed to an interactive format
        try: 
            format_change_dummy = 0
            if report_links[0][:22]!=report_links[1][:22]:
                format_change_dummy+=1
        except:
            problems.append(ticker)
            continue
        #obtain texts
        texts = []
        for i in report_links:
            html = urllib.request.urlopen(i).read().decode('utf-8')
            text = get_text(html)
            text = Clean(text)
            texts.append(text)
        #calculate cosine score and yoy % change in sentiment
        if len(texts)==2:
            sentiment_d = (TextBlob(texts[0]).sentiment.polarity-TextBlob(texts[1]).sentiment.polarity)/TextBlob(texts[1]).sentiment.polarity
            vec = CountVectorizer(input='content', stop_words='english')
            vectors = vec.fit_transform(texts)
            cosine = cosine_similarity(vectors[0],vectors[1]).item()
            scores.update({ticker:{'cosine':cosine, 'sentiment_d':sentiment_d,'format_change':format_change_dummy,'dates':filing_dates}})
        else:
            problems.append(ticker)
    #create dataframe and convert metrics to float
    df = pd.DataFrame.from_dict(scores).transpose()
    df.cosine = df.cosine.astype(float)
    df.sentiment_d = df.sentiment_d.astype(float)
    df['format_change'] = df['format_change'].astype(int) 
    #calculate number of workdays between month/day-filing dates
    df['date_delta'] = df.dates.apply(lambda x: workdays.networkdays(pd.to_datetime(x[0]),pd.to_datetime(x[1]))+262)
    #remove rows for reports filed more than one month after previous year's date to account for database errors
    problems += list(df[df.date_delta.abs()>31].index)
    df = df[df.date_delta.abs()<=31]
    #Create dummy for whether cosine score in bottom quintile of fall 2019 nyse and nasdaq equities
    new_cutoff = 0.07458812529222632
    old_cutoff = 0.9741300641628734
    df['bottom_quint']=0
    df[df['format_change']==0].bottom_quint = df[df['format_change']==0].cosine.apply(lambda x: 1 if x<=old_cutoff else 0)
    df[df['format_change']==1].bottom_quint = df[df['format_change']==1].cosine.apply(lambda x: 1 if x<=new_cutoff else 0)
    print('Reports unavailable for: ', problems)
    return df