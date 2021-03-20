{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import numpy as np\n",
    "import pandas as pd\n",
    "import pymysql\n",
    "from datetime import datetime, timedelta\n",
    "from sklearn.metrics import mean_squared_error\n",
    "import pmdarima as pm\n",
    "import os\n",
    "\n",
    "user = os.environ.get('DB_USER')\n",
    "password = os.environ.get('DB_PWD')\n",
    "db = os.environ.get('DB_DB')\n",
    "host = os.environ.get('DB_HOST')\n",
    "connection = pymysql.connect(host=host, user = user, passwd = password, port = 3306, db = db)\n",
    "\n",
    "df = pd.read_sql_query('SELECT incident_date, council_district, police_district, neighborhood FROM full_incidents',connection)\n",
    "\n",
    "df = df[df.incident_date >= '2020-01-01']\n",
    "\n",
    "connection.close()\n",
    "\n",
    "prediction = pd.DataFrame(columns=['location', 'level', 'frequency', 'start_date', 'end_date', 'pred', 'lower', 'upper'])\n",
    "performance = pd.DataFrame(columns=['entity', 'level', 'frequency', 'RMSE'])\n",
    "\n",
    "def insert_into_df(label, level, index, FORECAST, rmse, conf_int):\n",
    "    global prediction, performance\n",
    "    if len(index) == 365:\n",
    "        frequency = 'DAILY'\n",
    "    elif len(index) == 52:\n",
    "        frequency = 'WEEKLY'\n",
    "    elif len(index) == 12:\n",
    "        frequency = 'MONTHLY'\n",
    "    for i in range(len(index)):\n",
    "        if frequency == 'DAILY':\n",
    "            start_date = pd.to_datetime(index[i]).date()\n",
    "            end_date = pd.to_datetime(index[i]).date()\n",
    "        elif frequency == 'WEEKLY':\n",
    "            start_date = pd.to_datetime(index[i]).date()-timedelta(days=7)\n",
    "            end_date = pd.to_datetime(index[i]).date()\n",
    "        elif frequency == 'MONTHLY':\n",
    "            start_date = pd.to_datetime(index[i]).date()-timedelta(days=30)\n",
    "            end_date = pd.to_datetime(index[i]).date()\n",
    "        pred = FORECAST[i]\n",
    "        prediction = prediction.append({'location':label, 'level':level, 'frequency':frequency, 'start_date':start_date, 'end_date':end_date, 'pred':pred, 'lower':conf_int[i][0], 'upper':conf_int[i][1]}, ignore_index=True)   \n",
    "    performance = performance.append({'entity':label, 'level':level, 'frequency':frequency, 'RMSE':rmse}, ignore_index=True)\n",
    "\n",
    "def predict(data, index):\n",
    "    MODEL = pm.auto_arima(data, seasonal = False, error_action=\"raise\", stepwise=True, suppress_warnings=True, m=0)\n",
    "    FORECAST, conf_int = MODEL.predict(len(index), return_conf_int=True)\n",
    "    FORECAST = pd.Series(FORECAST, index = index)\n",
    "    return FORECAST, conf_int\n",
    "\n",
    "def validate_model(data):\n",
    "    data_train = data[:int(0.7*(len(data)))] \n",
    "    data_test = data[int(0.7*(len(data))):]\n",
    "    model = pm.auto_arima(data_train, seasonal = False, error_action=\"raise\", stepwise=True, suppress_warnings=True, m=0)\n",
    "    forecast = model.predict(len(data_test))\n",
    "    forecast = pd.Series(forecast, index = data_test.index)\n",
    "    rmse = np.sqrt(mean_squared_error(data_test['no_of_incidents'].values, forecast.values))\n",
    "    return rmse\n",
    "\n",
    "def daily(data, label, level):\n",
    "    rmse = validate_model(data)\n",
    "    index = pd.date_range(data.index[-1]+timedelta(days=1), freq = 'D', periods = 365)\n",
    "    FORECAST, conf_int = predict(data, index)\n",
    "    insert_into_df(label, level, index, FORECAST, rmse, conf_int)\n",
    "\n",
    "def weekly(data, label, level):\n",
    "    data_w = data.resample('W').sum()\n",
    "    rmse_w = validate_model(data_w)\n",
    "    index_w = pd.date_range(data_w.index[-1]+timedelta(days=7), freq = 'W', periods = 52)\n",
    "    FORECAST_w, conf_int = predict(data_w, index_w)\n",
    "    insert_into_df(label, level, index_w, FORECAST_w, rmse_w, conf_int)\n",
    "\n",
    "def monthly(data, label, level):\n",
    "    data_m = data.resample('M').sum()\n",
    "    rmse_m = validate_model(data_m)\n",
    "    index_m = pd.date_range(data_m.index[-1]+timedelta(days=30), freq = 'M', periods = 12)\n",
    "    FORECAST_m, conf_int = predict(data_m, index_m)\n",
    "    insert_into_df(label, level, index_m, FORECAST_m, rmse_m, conf_int)\n",
    "\n",
    "levels = ['council_district', 'police_district', 'neighborhood']\n",
    "for i in range(3):\n",
    "    df_level = df.iloc[:,[0,i+1]]\n",
    "    df_level = pd.DataFrame({'no_of_incidents' : df_level.groupby( [ df[levels[i]], df_level['incident_date'].dt.date] ).size()}).reset_index()\n",
    "    df_level = df_level.set_index('incident_date')\n",
    "    df_level = df_level[df_level[levels[i]] != '']\n",
    "    df_level = df_level[df_level[levels[i]] != 'UNKNOWN']\n",
    "    labels = df_level[levels[i]].unique()\n",
    "    for l in labels:\n",
    "        label_data = df_level[df_level[levels[i]]==l]\n",
    "        label_data = label_data[['no_of_incidents']]\n",
    "        label_data = label_data.asfreq('D')\n",
    "        label_data.no_of_incidents= label_data.no_of_incidents.fillna(0.0)\n",
    "        #Some neighborhood codes throwing errors, hence excluding them \n",
    "        try:\n",
    "            daily(label_data, l, levels[i])\n",
    "            weekly(label_data, l, levels[i])\n",
    "            monthly(label_data, l, levels[i])\n",
    "        except:\n",
    "            continue\n",
    "\n",
    "connection = pymysql.connect(host=host, user = user, passwd = password, port = 3306, db = db)\n",
    "cur = connection.cursor()\n",
    "\n",
    "cur.execute(\"TRUNCATE TABLE predictions\")\n",
    "cur.execute(\"TRUNCATE TABLE performance\")\n",
    "connection.commit()\n",
    "\n",
    "for (row,rs) in performance.iterrows():\n",
    "    rs[3] = str(rs[3])\n",
    "    cur.execute(\"INSERT INTO performance(entity, level, freq, rmse) VALUES('\"+rs[0]+\"', '\"+rs[1]+\"', '\"+rs[2]+\"', \"+rs[3]+\")\")   \n",
    "\n",
    "for (row,rs) in prediction.iterrows():\n",
    "    rs[3] = rs[3].strftime('%Y-%m-%d')\n",
    "    rs[4] = rs[4].strftime('%Y-%m-%d')\n",
    "    rs[5] = str(rs[5])\n",
    "    rs[6] = str(rs[6])\n",
    "    rs[7] = str(rs[7])\n",
    "    cur.execute(\"INSERT INTO predictions(location, level, freq, start_date, end_date, predicted_incidents, lower_predicted_incidents, upper_predicted_incidents) VALUES('\"+rs[0]+\"', '\"+rs[1]+\"', '\"+rs[2]+\"', '\"+rs[3]+\"', '\"+rs[4]+\"', \"+rs[5]+\", \"+rs[6]+\", \"+rs[7]+\")\")\n",
    "\n",
    "connection.commit()\n",
    "\n",
    "connection.close()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
