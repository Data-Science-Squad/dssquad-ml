#!/usr/bin/env python
# coding: utf-8

# In[68]:


import numpy as np
import pandas as pd
import pymysql
from sklearn.metrics import mean_squared_error, mean_absolute_error
import pmdarima as pm
from pmdarima.model_selection import train_test_split
get_ipython().run_line_magic('matplotlib', 'inline')
from statsmodels.tsa.arima_model import ARIMA
from matplotlib import pyplot as plt
import seaborn as sns
import os


# In[69]:


user = os.environ.get('DB_USER')
password = os.environ.get('DB_PWD')


# In[70]:


connection = pymysql.connect(host='caskeycoding.com', user = user, passwd = password, port = 3306, db = 'caskey5_buffaloCrime')


# In[72]:


df = pd.read_sql_query('SELECT incident_date, police_district FROM full_incidents',connection)


# In[73]:


df.head()


# In[74]:


df = pd.DataFrame({'no_of_incidents' : df.groupby( [ df.police_district, df.incident_date.dt.date] ).size()}).reset_index()


# In[75]:


df


# In[76]:


df.police_district.unique()


# In[77]:


data_A = df[df['police_district'] == 'District A']
data_B = df[df['police_district'] == 'District B']
data_C = df[df['police_district'] == 'District C']
data_D = df[df['police_district'] == 'District D']
data_E = df[df['police_district'] == 'District E']


# In[78]:


data_A


# In[79]:


arr = [data_A, data_B, data_C, data_D, data_E]


# In[80]:


train = [None] * 5
test = [None] * 5


# ## Preprocessing the data

# In[81]:


for i in range(5):
    arr[i] = arr[i].loc[:,['incident_date', 'no_of_incidents']]
    arr[i].set_index('incident_date', inplace = True)
    arr[i] = arr[i].asfreq('D')
    arr[i].no_of_incidents= arr[i].no_of_incidents.fillna(0.0)
    arr[i] = arr[i][arr[i].index >= '2009-01-01']
    arr[i] = arr[i].resample('W-SUN').sum()
    train[i]=arr[i][arr[i].index < arr[i].index[-4]]
    test[i]=arr[i][arr[i].index >= arr[i].index[-4]]


# In[82]:


train[0].shape


# In[83]:


test[0].shape


# In[84]:


index_val = pd.date_range(train[0].index[-1], freq = 'W', periods = 4)
index_val


# In[85]:


arima_models_val = [None] * 5
arima_forecasts_val = [None] * 5


# ## Applying and validating ARIMA

# In[86]:


for i in range(5):
    arima_models_val[i] = pm.auto_arima(train[i], seasonal = False, m=0)
    arima_forecasts_val[i] = arima_models_val[i].predict(4)
    arima_forecasts_val[i] = pd.Series(arima_forecasts_val[i], index = index_val)
    arima_forecasts_val[i] = arima_forecasts_val[i].rename("Auto Arima")
    fig, ax = plt.subplots(figsize = (20,5))
    chart = sns.lineplot(x='incident_date', y='no_of_incidents', data=train[i])
    test[i].plot(ax=ax, color='blue', marker='o', legend=True)
    arima_forecasts_val[i].plot(ax=ax, color='red', marker='o', legend=True)


# In[87]:


arima_rmse = [None] * 5
arima_mae = [None] * 5


# In[88]:


for i in range(5):
    arima_rmse[i] = np.sqrt(mean_squared_error(test[i]['no_of_incidents'].values, arima_forecasts_val[i].values))
    arima_mae[i] = mean_absolute_error(test[i]['no_of_incidents'].values, arima_forecasts_val[i].values)


# In[89]:


print('RMSE')
print(arima_rmse)
print('MAE')
print(arima_mae)


# ## Prediction for the next 4 weeks

# In[90]:


index = pd.date_range(test[0].index[-1], freq = 'W', periods = 4)
index


# In[91]:


arima_models= [None] * 5
arima_forecasts= [None] * 5


# In[92]:


for i in range(5):
    arima_models[i] = pm.auto_arima(train[i], seasonal = False, m=0)
    arima_forecasts[i] = arima_models[i].predict(4)
    arima_forecasts[i] = pd.Series(arima_forecasts[i], index = index)
    arima_forecasts[i] = arima_forecasts[i].rename("Auto Arima")
    fig, ax = plt.subplots(figsize = (20,5))
    chart = sns.lineplot(x='incident_date', y='no_of_incidents', data=arr[i])
    arima_forecasts[i].plot(ax=ax, color='red', marker='o', legend=True)

