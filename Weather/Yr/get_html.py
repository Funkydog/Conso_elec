#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 29 13:21:13 2017

@author: anordvik
"""

from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import datetime as dt
import os

path=os.getcwd()
weather_path="../../Weather/Yr"
weather_file="statistics_yr.csv"

def last_date():
    weather_stat = pd.read_csv(path + "/" + weather_path + "/" + weather_file, sep="\t")
    weather_stat['Dato'] = pd.to_datetime(weather_stat.Dato, format='%Y-%m-%d')
    last_ind = weather_stat.last_valid_index()
    return weather_stat.Dato[last_ind].date().strftime('%B %d, %Y')

url = 'https://www.yr.no/place/Norway/Oslo/Oslo/Oslo/detailed_statistics.html'

def update_data(last_date=last_date()):
    if pd.to_datetime(last_date).date() != pd.datetime.now().date()-dt.timedelta(1):
        text_soup = BeautifulSoup(urlopen(url).read(),"html.parser") #read in URL
        datas = text_soup.findAll('tr') #Find table
        
        for data in datas:
            if last_date in data.text:
                update=pd.DataFrame([td.text.splitlines() for td in data.find_previous_siblings('tr') if td.text])
                
        update=update.drop(0,axis=1)
        update[1]=pd.to_datetime(update[1])
        mapping={' ':'','°':'','mm':'','cm':'','m/s':''}
        update=update.replace(mapping,regex=True)
        #Add new data to the CSV :
        update.to_csv(path + "/" + weather_path + "/" + weather_file, sep="\t",header=False, index=False, mode='a',index_label=False)
        
        print("File Updated from {date}".format(date=last_date))
    else:
        print("File already updated today, try again tomorrow")