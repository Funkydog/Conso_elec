#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 18:04:36 2017

@author: anordvik
"""

import pandas as pd
import datetime as dt
from bokeh.plotting import figure, output_file, show
import bokeh.models as bkm
import os

path=os.getcwd()
weather_path="Weather/Yr"
file="Inkognito_elec.csv"
weather_file="statistics_yr.csv"

elec_price = 0.8238 #NOK/kWh
m_CO2 = 0.017 #Kg/KWh in Norway 2015
confort_T = 18 #˚C

def run():
    global conso_elec 
    weather_stat = pd.read_csv(path + "/" + weather_path + "/" + weather_file, sep="\t")
    conso_elec = pd.read_csv(path + "/" + file)
    #If last update was more than 15 days ago: Update
    days_between_update=15 # >2 and <28
    if pd.datetime.now().date() - pd.to_datetime(weather_stat.Dato[weather_stat.last_valid_index()]).date() >= dt.timedelta(days_between_update-2):
        exec(open(path + "/" + weather_path + "/" + "get_html.py").read())
        update_data() #Updates weather_stat from Yr.no every 15 days
        weather_stat = pd.read_csv(path + "/" + weather_path + "/" + weather_file, sep="\t")
    return (conso_elec, weather_stat)


def last_conso():
    """Returns the last mesure writen in the database with its date"""
    (conso_elec, weather_stat) = run()
    conso_elec['date'] = pd.to_datetime(conso_elec.date)
    conso_elec = conso_elec.sort_values(by='date')
    last_ind = conso_elec.last_valid_index()
    last_time = conso_elec.date[last_ind].date()
    
    last_mesure=pd.datetime.now().date() - last_time
    last_cons=conso_elec.conso[last_ind]
    print("Last mesure was taken {days} days ago: {last_cons} kWh".format(days=last_mesure.days,last_cons=last_cons))
    return (last_cons,last_time)

        

def new_conso(conso, date = dt.datetime.now().date()):
    (last_cons,last_time) = last_conso()
    date_c=pd.to_datetime(date)
    if date_c.date() - last_time >= dt.timedelta(0):
        if conso > last_cons:
            run()
            df=pd.DataFrame([(conso,date)], columns=conso_elec.columns)
            newconso=conso_elec.append(df, ignore_index=True)
            newconso.to_csv(path +"/"+ file, index=False)
        else:
            run()
            newconso='Not enough'
            print("La conso est inferieur a la conso precedante, veuillez rentree une nouvelle valeur")
    else:
        run()
        newconso='Wrong date'
        print("La date de conso ne correspond pas avec la date attendue")
    return newconso


def print_html():  
    conso_elec, weather_stat = run()
    
    conso_elec['date_c'] = pd.to_datetime(conso_elec.date)
    conso_elec = conso_elec.sort_values(by='date_c')
    conso_elec = conso_elec.reset_index(drop=True)
    weather_stat['Dato'] = pd.to_datetime(weather_stat.Dato, format='%Y-%m-%d')
    
    if any(conso_elec.conso.diff()<0):
        l=(conso_elec.conso.diff()<0)
        ind=[i for i,l in enumerate(l) if l]# Give the index of the error line
        d=conso_elec.date[ind]
        print("Your database contains an error, please check the values arround {d}".format(d=d))
        
    
    #Group by all conso in the same month, and take the last value to substract with previous month
    grp = conso_elec.groupby([conso_elec.date_c.dt.year, conso_elec.date_c.dt.month])
    res = grp.last()
    res.conso = res.conso.diff()
    
    #Group all the initial values
    #Conso
    x = res.date_c
    y = res.conso
    #Weather from Yr.no
    x_data = weather_stat.Dato
    y_min = weather_stat.Min_T
    y_max = weather_stat.Maks_T
    y_mean = weather_stat.Middel_T
    y_normal = weather_stat.Normal_T
    
    
    p = figure(plot_width=800, plot_height=500, y_axis_label="Energy consumed in kWh/month", x_axis_type="datetime", tools="resize,save", toolbar_location="above", title="Electrical consumption at Inkognito, Oslo")

    #Add second axis
    p.extra_y_ranges = {"Temp" : bkm.Range1d(start=min(y_min-5), end=max(y_max+5))}
    p.add_layout(bkm.LinearAxis(y_range_name="Temp"),'right')
    
    #Source1 gets the conso values and print it with its hover method
    source1= bkm.ColumnDataSource(data={"x": x, "y": y, "bill":y*elec_price, "CO2":y*m_CO2, "time_tooltip":res.date})
    g1 = bkm.VBar(x='x', top='y', width=1e9, bottom=0, fill_color='green')
    g1_r = p.add_glyph(source_or_glyph=source1, glyph=g1)
    g1_hover = bkm.HoverTool(renderers=[g1_r], tooltips={
        "Conso": "@y kWh",
        "Bill":"±@bill{int} NOK",
        "CO2 prod.":"@CO2{int} Kg",            
        "Date": "@time_tooltip"
    })
    p.add_tools(g1_hover)
    
    #Creates a dictionnary with the weather data and ads a tooltip column for the date hover
    data={"x_data": x_data, 
          "y_min": y_min,
          "y_max": y_max,
          "y_mean": y_mean,
          "DJU":confort_T-y_mean
          }
    #Convert the date into a string to be read in the hover
    df=pd.DataFrame(data)
    df['tooltip'] = [x.strftime("%Y-%m-%d") for x in df['x_data']]
    #Source2 does the same as source1 with the temperatures
    source2= bkm.ColumnDataSource(df)
    g2 = bkm.Line(x='x_data', y='y_mean',line_color='orange',name="Avg_temp" , line_alpha=0.9)
    g2_r = p.add_glyph(source_or_glyph = source2, glyph = g2, y_range_name="Temp")
    g2_hover = bkm.HoverTool(renderers = [g2_r], tooltips={
        "Avg. Temp.": "$y ˚C",
        "DJU": "@DJU{int}",
        "Date": "@tooltip"
    })
    p.add_tools(g2_hover)
    
    p.line(x_data,y_max, y_range_name="Temp", legend="max_temp",color='red', line_alpha=0.5, line_dash='dashdot')
    p.line(x_data,y_min, y_range_name="Temp",legend="min_temp", color='blue', line_alpha=0.5, line_dash='dashdot')
    p.line(x_data,y_normal, y_range_name="Temp",legend="normal_temp", color='black', line_alpha=1, line_dash='dashed')
    

    output_file("index.html", title="Inkognito_conso")
    show(p)
