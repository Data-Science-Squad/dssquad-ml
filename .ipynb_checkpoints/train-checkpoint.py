#!/usr/bin/env python
# coding: utf-8

# In[34]:


import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error
import pmdarima as pm
import os


# In[53]:


user = os.environ.get('DB_USER')
password = os.environ.get('DB_PWD')
db = os.environ.get('DB_DB')
host = os.environ.get('DB_HOST')


# In[71]:


sqlEngine = create_engine('mysql+pymysql://{}:{}@{}:3306/{}'.format(user,password,host,db), pool_recycle=3600)
connection = sqlEngine.connect()

df = pd.read_sql_query('SELECT incident_date, council_district, police_district, neighborhood FROM full_incidents',connection)
df = df[df.incident_date >= '2020-01-01']

connection.close()


# In[38]:


prediction = pd.DataFrame(columns=['location', 'level', 'frequency', 'start_date', 'end_date', 'pred', 'lower', 'upper'])
performance = pd.DataFrame(columns=['entity', 'level', 'frequency', 'RMSE'])


# In[8]:


def insert_into_df(label, level, index, FORECAST, rmse, conf_int):
    global prediction, performance
    if len(index) == 365:
        frequency = 'DAILY'
    elif len(index) == 52:
        frequency = 'WEEKLY'
    elif len(index) == 12:
        frequency = 'MONTHLY'
    for i in range(len(index)):
        if frequency == 'DAILY':
            start_date = pd.to_datetime(index[i]).date()
            end_date = pd.to_datetime(index[i]).date()
        elif frequency == 'WEEKLY':
            start_date = pd.to_datetime(index[i]).date()-timedelta(days=7)
            end_date = pd.to_datetime(index[i]).date()
        elif frequency == 'MONTHLY':
            start_date = pd.to_datetime(index[i]).date()-timedelta(days=30)
            end_date = pd.to_datetime(index[i]).date()
        pred = FORECAST[i]
        prediction = prediction.append({'location':label, 'level':level, 'frequency':frequency, 'start_date':start_date, 'end_date':end_date, 'pred':pred, 'lower':conf_int[i][0], 'upper':conf_int[i][1]}, ignore_index=True)   
    performance = performance.append({'entity':label, 'level':level, 'frequency':frequency, 'RMSE':rmse}, ignore_index=True)


# In[10]:


def predict(data, index):
    MODEL = pm.auto_arima(data, seasonal = False, error_action="raise", stepwise=True, suppress_warnings=True, m=0)
    FORECAST, conf_int = MODEL.predict(len(index), return_conf_int=True)
    FORECAST = pd.Series(FORECAST, index = index)
    return FORECAST, conf_int


# In[11]:


def validate_model(data):
    data_train = data[:int(0.7*(len(data)))] 
    data_test = data[int(0.7*(len(data))):]
    model = pm.auto_arima(data_train, seasonal = False, error_action="raise", stepwise=True, suppress_warnings=True, m=0)
    forecast = model.predict(len(data_test))
    forecast = pd.Series(forecast, index = data_test.index)
    rmse = np.sqrt(mean_squared_error(data_test['no_of_incidents'].values, forecast.values))
    return rmse


# In[12]:


def daily(data, label, level):
    rmse = validate_model(data)
    index = pd.date_range(data.index[-1]+timedelta(days=1), freq = 'D', periods = 365)
    FORECAST, conf_int = predict(data, index)
    insert_into_df(label, level, index, FORECAST, rmse, conf_int)


# In[13]:


def weekly(data, label, level):
    data_w = data.resample('W').sum()
    rmse_w = validate_model(data_w)
    index_w = pd.date_range(data_w.index[-1]+timedelta(days=7), freq = 'W', periods = 52)
    FORECAST_w, conf_int = predict(data_w, index_w)
    insert_into_df(label, level, index_w, FORECAST_w, rmse_w, conf_int)


# In[14]:


def monthly(data, label, level):
    data_m = data.resample('M').sum()
    rmse_m = validate_model(data_m)
    index_m = pd.date_range(data_m.index[-1]+timedelta(days=30), freq = 'M', periods = 12)
    FORECAST_m, conf_int = predict(data_m, index_m)
    insert_into_df(label, level, index_m, FORECAST_m, rmse_m, conf_int)


# In[50]:


levels = ['council_district', 'police_district', 'neighborhood']
for i in range(3):
    df_level = df.iloc[:,[0,i+1]]
    df_level = pd.DataFrame({'no_of_incidents' : df_level.groupby( [ df[levels[i]], df_level['incident_date'].dt.date] ).size()}).reset_index()
    df_level = df_level.set_index('incident_date')
    df_level = df_level[df_level[levels[i]] != '']
    df_level = df_level[df_level[levels[i]] != 'UNKNOWN']
    labels = df_level[levels[i]].unique()
    for l in labels:
        label_data = df_level[df_level[levels[i]]==l]
        label_data = label_data[['no_of_incidents']]
        label_data = label_data.asfreq('D')
        label_data.no_of_incidents= label_data.no_of_incidents.fillna(0.0)
        #Some neighborhood codes throwing errors, hence excluding them 
        try:
            daily(label_data, l, levels[i])
            weekly(label_data, l, levels[i])
            monthly(label_data, l, levels[i])
        except:
            continue


# In[72]:


sqlEngine = create_engine('mysql+pymysql://{}:{}@{}:3306/{}'.format(user,password,host,db), pool_recycle=3600)
connection = sqlEngine.connect()

performance.to_sql('performance', con=connection, if_exists='replace', index=False)
prediction.to_sql('predictions', con=connection, if_exists='replace', index=False)

connection.close()

