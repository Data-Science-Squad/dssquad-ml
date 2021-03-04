
library(tidyverse)
library(lubridate)
library(DBI)
library(odbc)
library(RMySQL)
library(prophet)
library(furrr)

####################
## Database query ##
####################

creds <- readLines("C:/Users/Owner/Documents/data-science-projects/ds-squad/creds.txt")

conn <- dbConnect(
  MySQL(), 
  user=creds[1], 
  password=creds[2], 
  dbname='caskey5_buffaloCrime', 
  host=creds[3]
)

base_query <- tbl(conn, "full_incidents") %>%
  filter(incident_date >= "2015-01-01") %>%
  collect() %>%
  mutate(City = "Buffalo") %>%
  mutate(incident_date = as.Date(incident_date)) %>%
  mutate(incident_week = floor_date(incident_date, unit = "week")) %>%
  mutate(incident_month = floor_date(incident_date, unit = "month")) 

dbDisconnect(conn)

#######################
## Data Aggregations ##
#######################

# generic function to count incidents for any date interval and geo type
summarize_incidents <- function(date_var, area_type, freq) {
  base_query %>%  
    rename(date = date_var, area = area_type) %>%
    group_by(date, area) %>%
    summarise(Incidents = n_distinct(case_number))  %>%
    ungroup() %>%
    mutate(Geo_Level = area_type) %>%
    mutate(Freq = freq) %>%
    select(model_date = date,
           Geo = area,
           Geo_Level,
           Freq,
           Incidents)
}

# Daily data 
all_daily <- summarize_incidents("incident_date", "City", "daily")
police_daily <- summarize_incidents("incident_date", "police_district", "daily")

# Weekly data 
all_weekly = summarize_incidents("incident_week", "City", "weekly")
police_weekly = summarize_incidents("incident_week", "police_district", "weekly")
council_weekly = summarize_incidents("incident_week", "council_district", "weekly")

# Monthly data 
all_monthly = summarize_incidents("incident_month", "City", "monthly")
police_monthly = summarize_incidents("incident_month", "police_district", "monthly")
council_monthly = summarize_incidents("incident_month", "council_district", "monthly")
nbor_monthly = summarize_incidents("incident_month", "neighborhood", "monthly")

###################
## Modeling data ##
###################

all_data_assets <- list(
  all_daily,
  police_daily,
  all_weekly,
  police_weekly,
  council_weekly,
  all_monthly,
  police_monthly,
  council_monthly,
  nbor_monthly
)

model_df <- bind_rows(all_data_assets) %>%
  filter(!is.na(Geo),
         Geo != "",
         Geo != "UNKNOWN")

model_df %>%
  select(Geo_Level, Freq) %>%
  distinct()

model_splits <- model_df %>%
  group_by(Geo, Geo_Level, Freq) %>%
  group_split()

#############
## Prophet ##
#############

prophet_function <- function(train_df, test_df) {
  # Define prophet model parameters (defaults)
  fit_spec <- prophet(
    growth = "linear",
    yearly.seasonality = "auto",
    weekly.seasonality = "auto",
    daily.seasonality = "auto"
  )
  # Fit prophet model to training data
  fit <-  fit.prophet(fit_spec, train_df)
  # Get forecasts and lower/upper limits of 95% CI
  fcast <- predict(fit, df = test_df) %>%
    select(yhat, yhat_lower, yhat_upper)
  # Output
  return(fcast)
}

prophet_models <- future_map(model_splits, function(i) {
  
  # Train/test splits
  train <- i %>% filter(model_date <= "2019-12-31") 
  test <- i %>% filter(model_date >= "2020-01-01", 
                       model_date <= "2020-12-31")
  
  # Convert train/test to prophet format
  prophet_train <- train %>% select(ds = model_date, y = Incidents)
  prophet_test <- test %>% select(ds = model_date, y = Incidents)
  
  # Fit/predict
  prophet_fcast <- prophet_function(
    train_df = prophet_train, 
    test_df = prophet_test
  )
  
  # Append predictions to testing data
  test_with_pred <- test %>% bind_cols(prophet_fcast)
  
  # Output
  out <- bind_rows(
    train %>% mutate(Split = "Train"), 
    test_with_pred %>% mutate(Split = "Test")
  )
  
  return(out)
}) %>%
  bind_rows()

write_csv(prophet_models, "prophet-demo/prophet_forecasts.csv")
write_csv(model_df, "prophet-demo/model_data.csv")

prophet_models %>%
  plot_ly(x = ~model_date) %>%
  add_lines(y = ~Incidents, name = "actual", line = list(color = 'gray')) %>%
  add_lines(y = ~yhat, name = "yhat", line = list(color = 'blue')) %>%
  add_lines(y = ~yhat_lower, name = "lower_bound", line = list(color = 'green')) %>%
  add_lines(y = ~yhat_upper, name = "upper_bound", line = list(color = 'red'))

