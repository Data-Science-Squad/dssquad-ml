Introduction

Our problem statement is to forecast the number of crimes based on some geographical unit. This problem could be treated as a simple regression problem or a time series problem. Although this problem can also be solved using linear regression, it isn’t the best approach as it neglects the relation of the values with all the relative past values (which is of prime importance while forecasting crimes).

Time Series Analysis

Time Series is a series of observations taken at equal intervals of time. It is used to predict future values based on past observed values. The components that we might observe in the time-series analysis are Trend, Seasonality, Irregularity, and Cyclicity.
Our dataset is a case of ‘Univariate Time Series’ as we’ll be observing only one variable (i.e. geographical unit) at a time. 

ARIMA

ARIMA is a very popular statistical method for time series forecasting. ARIMA stands for Auto-Regressive Integrated Moving Averages. ARIMA models work on the following assumptions:

•	The data series is stationary, i.e. the mean and variance should not vary with time. A series can be made stationary by using log transformation or differencing the series.

•	The data provided as input must be a Univariate series, since Arima uses past values to predict the future values.

ARIMA has three components – AR (autoregressive term), I (differencing term) and MA (moving average term).

•	AR term refers to the past values used for forecasting the next value. The AR term is defined by the parameter ‘p’ in Arima. The value of ‘p’ is determined using the PACF plot.

•	MA term is used to define the number of past forecast errors used to predict the future values. The parameter ‘q’ in Arima represents the MA term. The ACF plot is used to identify the correct ‘q’ value.

•	The Order of differencing specifies the number of times the differencing operation is performed on the series to make it stationary. The ADF and KPSS tests are used to determine whether the series is stationary and help in identifying the‘d’ value.

Auto ARIMA

Although ARIMA is a very powerful model for forecasting time series data, the data preparation and parameter tuning processes are quite time consuming. Before we implement ARIMA, we need to make the series stationary, determine ‘d’ value, create ACF and PACF plots, and determine the values of ‘p’ and ‘q’. Auto ARIMA automates all these tasks for us. 
Auto ARIMA takes into account the AIC and BIC values generated to determine the best combination of parameters. AIC (Akaike Information Criterion) and BIC (Bayesian Information Criterion) values are estimators to compare models. The lower these values, the better is the model.

Implementation
1.	Load the data: We fetch the required columns from the database. We group the dataset by number of crimes committed each day.
2.	Data preprocessing: After visualizing the data, we only consider the data after 2009 and convert it into a time series by setting ‘incident date’ as frequency, frequency as daily, and filling the null values.
3.	Fit Auto ARIMA: We split the data into training and validation data and fit the auto_arima model on the training data. 
4.	Validate the model: We visualize the result by plotting the forecasted data on top of the validation data.
5.	Evaluate the model: We check the performance of the model using forecasted values against actual (validation) values using RMSE.
6.	Apply Forecast: We apply the auto_arima model on the entire data and save the forecasted values back into the database.

Evaluation Metric

The Root Mean Squared Error (RMSE) is defined as the square root of the average squared error. Compared to MAE (Mean Absolute Error) RMSE does not treat each error the same. RMSE emphasizes the most significant errors, hence one big error will be enough to give a very bad RMSE. While MAE protects outliers, RMSE assures us to get an unbiased forecast.

Model’s Strengths

The input data is univariate and tested for stationarity as well as seasonality. The input data is resampled, so as to fit the model best.

Model’s Weakness

We have used a univariate time-series to solve our problem. That means we are only considering the relationship between the y-axis value and the x-axis time points. We are not considering outside factors like holidays, weather, etc. that may be affecting the forecast.
