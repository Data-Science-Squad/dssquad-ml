#!/usr/bin/env python
# coding: utf-8

# ## Libraries

# In[ ]:


import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error
import pmdarima as pm
import os


# ## Database connection

# In[8]:


def db_connect():
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PWD')
    db = os.environ.get('DB_DB')
    host = os.environ.get('DB_HOST')
    sqlEngine = create_engine('mysql+pymysql://{}:{}@{}:3306/{}'.format(user,password,host,db), pool_recycle=3600)
    connection = sqlEngine.connect()
    return(connection)


# ## Get data

# In[32]:


def get_df():
    connection = db_connect()
    df_query = "SELECT incident_date, council_district, police_district, neighborhood FROM full_incidents WHERE incident_date >= '2020-01-01'"
    df = pd.read_sql_query(df_query,connection) 
    connection.close()
    return(df)

print("Getting data")
df = get_df()


# ## Create Dataframes for predictions and performance metrics

# In[33]:


print("Creating prediction and performance Dataframes")
prediction = pd.DataFrame(columns=['location', 'level', 'frequency', 'start_date', 'end_date', 'pred', 'lower', 'upper'])
performance = pd.DataFrame(columns=['entity', 'level', 'frequency', 'RMSE'])


# ## Modeling functions

# In[22]:


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


# In[23]:


def predict(data, index):
    MODEL = pm.auto_arima(data, seasonal = False, error_action="raise", stepwise=True, suppress_warnings=True, m=0)
    FORECAST, conf_int = MODEL.predict(len(index), return_conf_int=True)
    FORECAST = pd.Series(FORECAST, index = index)
    return FORECAST, conf_int


# In[24]:


def validate_model(data):
    data_train = data[:int(0.7*(len(data)))] 
    data_test = data[int(0.7*(len(data))):]
    model = pm.auto_arima(data_train, seasonal = False, error_action="raise", stepwise=True, suppress_warnings=True, m=0)
    forecast = model.predict(len(data_test))
    forecast = pd.Series(forecast, index = data_test.index)
    rmse = np.sqrt(mean_squared_error(data_test['no_of_incidents'].values, forecast.values))
    return rmse


# In[25]:


def daily(data, label, level):
    rmse = validate_model(data)
    index = pd.date_range(data.index[-1]+timedelta(days=1), freq = 'D', periods = 365)
    FORECAST, conf_int = predict(data, index)
    insert_into_df(label, level, index, FORECAST, rmse, conf_int)


# In[26]:


def weekly(data, label, level):
    data_w = data.resample('W').sum()
    rmse_w = validate_model(data_w)
    index_w = pd.date_range(data_w.index[-1]+timedelta(days=7), freq = 'W', periods = 52)
    FORECAST_w, conf_int = predict(data_w, index_w)
    insert_into_df(label, level, index_w, FORECAST_w, rmse_w, conf_int)


# In[27]:


def monthly(data, label, level):
    data_m = data.resample('M').sum()
    rmse_m = validate_model(data_m)
    index_m = pd.date_range(data_m.index[-1]+timedelta(days=30), freq = 'M', periods = 12)
    FORECAST_m, conf_int = predict(data_m, index_m)
    insert_into_df(label, level, index_m, FORECAST_m, rmse_m, conf_int)


# ## Train, forecast, and measure model performance

# In[36]:


print("Training, forecasting, and measuring...")

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


# ## Write outputs

# In[34]:


def write_to_db(df, table_name):
    connection = db_connect()
    df.to_sql(table_name, con=connection, if_exists='replace', index=False)
    connection.close()
    return None

print("Writing outputs")
write_to_db(df=performance, table_name="performance")
write_to_db(df=prediction, table_name="prediction")

