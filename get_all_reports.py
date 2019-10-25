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

#Get the links for the 10-K index pages for each company
def get_all_links(tickers, k_or_q='k'):    
    hrefs = {}
    for ticker in tqdm(tickers):
        if k_or_q=='k':
            rss = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + str(ticker) +'&type=10-k%25&dateb=&owner=exclude&start=0&count=40&output=atom'
        else:
            rss = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + str(ticker) +'&type=10-q%25&dateb=&owner=exclude&start=0&count=40&output=atom'
        page = requests.get(rss)
        filing_dates = [i.string for i in BeautifulSoup(page.content, 'html.parser').find_all('filing-date')]
        indices = [i.string for i in BeautifulSoup(page.content, 'html.parser').find_all('filing-href')]
        report_links = {}
        for i in range(len(indices)):
            page = requests.get(indices[i])
            index_links = [j.get('href') for j in BeautifulSoup(page.content,'html.parser').find_all('a')]
            index_links = [j for j in index_links if ('/Archives/edgar/data' in j) & (j[-4:]=='.htm')]
            if len(index_links)>0:
                link = 'https://www.sec.gov' + index_links[0]
                report_links.update({filing_dates[i]:link})
        hrefs.update({ticker:report_links})
    return hrefs 

def get_metrics(links):
    vec = CountVectorizer(input='content', stop_words='english')
    dic = {}
    problems = {}
    for ticker in tqdm(links):
        try:
            texts = []
            single_dates = []
            for date in links[ticker]:
                try:
                    html = urllib.request.urlopen(links[ticker][date]).read().decode('utf-8')
                    text = get_text(html)
                    text = Clean(text)
                    texts.append(text)
                    single_dates.append(date)
                except:
                    texts.append('problem')
                    single_dates.append(date)
            problem_inds = [ind for ind, val in enumerate(texts) if val=='problem']
            good_inds = [ind for ind, val in enumerate(texts) if val!='problem']
            texts = [texts[i] for i in good_inds]           
            dates = [(single_dates[i],single_dates[i+1]) for i in range(len(single_dates)-1)]
            problem_dates = [dates[i] for i in problem_inds]
            good_dates = [dates[i] for i in good_inds]
       
            cosines = []
            sentiments = []
            for text in texts:
                 sentiments.append(TextBlob(texts).sentiment.polarity)
            sentiment_deltas = [(sentiments[i]-sentiments[i+1])/sentiments[i+1] for i in range(len(sentiments)-1)]
            vectors = vec.fit_transform(texts)
            for i in range(vectors.shape[0]-1):
                cosines.append(cosine_similarity(vectors[i],vectors[i+1]).item())
            dic.update({ticker:[{'dates':good_dates,'sentiment_ds':sentiment_deltas},{'cosine_score':cosines}]})
            problems.update({ticker:problem_dates})
            df = pd.DataFrame.from_dict(dic)
        except:
            problems.update({ticker:'total failure'})
    return dic, problems