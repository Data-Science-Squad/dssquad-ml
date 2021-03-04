library(shinyWidgets)
library(shiny)
library(tidyverse)
library(plotly)

forecasts_tbl <- read_csv("https://raw.githubusercontent.com/Data-Science-Squad/dssquad-ml/dm-model/prophet-demo/prophet_models.csv")

geo_levels <- unique(forecasts_tbl$Geo_Level)

geos <- forecasts_tbl %>%
    pull(Geo_Level) %>%
    unique()

freqs <- forecasts_tbl %>%
    pull(Geo_Level) %>%
    unique()

ui <- fluidPage(
    titlePanel("Forecasting multiple geographies and time intervals using Prophet"),
    br(),
    p("The models for this app were run offline and the predictions are precompiled in a CSV."),
    p("The data used for modeling is here: ", tags$a(href = "https://raw.githubusercontent.com/Data-Science-Squad/dssquad-ml/dm-model/prophet-demo/model_data.csv", "https://raw.githubusercontent.com/Data-Science-Squad/dssquad-ml/dm-model/prophet-demo/model_data.csv")),
    br(),
    fluidRow(
        column(4, selectInput("geo_level", "Select a geographical unit", geo_levels, selected = 'City')),
        column(4, pickerInput("geo", "Select a location", choices = "", options = list(title = "location"))),
        column(4, pickerInput("freq", "Select a frequency", choices = "", options = list(title = "frequency")))
    ),
    br(),
    shiny::actionButton("button", "Run App", class = "btn-warning"),
    hr(),
    # sidebarLayout(
    #     sidebarPanel(
    #         width = 4,
    #         HTML("<span class='title'>Explore WFM Forecasting</span>"),
    #         selectInput("geo_level", "Select a geo hierarchy", geo_levels),
    #         pickerInput("geo", choices = "", options = list(title = "Select a geo")),
    #         pickerInput("freq", choices = "", options = list(title = "Select a frequency")),
    #         tags$br(),
    #         tags$br(),
    #         shiny::actionButton("button", "Run App", icon = shiny::icon("power-off", class = "power")),
    #         shiny::downloadButton("download", "Download Results"),
    #         tags$p("Updated:", Sys.time())
    #     ),
    plotly::plotlyOutput("plot_out", height = 300)
#)
)
server <- function(input, output, session) {
    
    geo_level_df <- eventReactive(input$geo_level, {
        geo_level_df <- forecasts_tbl %>%
            filter(Geo_Level == input$geo_level)
    })
    
    observeEvent(input$geo_level, {
        updatePickerInput(
            session = session,
            inputId = "geo",
            choices = unique(geo_level_df()$Geo)
        )
        updatePickerInput(
            session = session,
            inputId = "freq",
            choices = unique(geo_level_df()$Freq)
        )
    })
    
    observeEvent(input$button, {
        
        selected_geo <- forecasts_tbl %>%
            filter(Geo_Level == input$geo_level, 
                   Geo == input$geo,
                   Freq == input$freq)
        
        p <- selected_geo %>%
            plot_ly(x = ~model_date) %>%
            add_lines(y = ~Incidents, name = "actual", line = list(color = '#dbdbdb')) %>%
            add_lines(y = ~yhat, name = "yhat", line = list(color = 'orange')) %>%
            add_lines(y = ~yhat_lower, name = "lower_bound", line = list(color = '#e683df')) %>%
            add_lines(y = ~yhat_upper, name = "upper_bound", line = list(color = '#ed6fa4'))
        
        output$plot_out <- renderPlotly({
            p
        })
        
        # # Log file: date-time, filenames, sizes, outcome
        # bucket <- "hnny-data-analytics-sandbox"
        # current_dt <- format(Sys.time()-14400, "%Y%m%d%H%M%S")
        # key <- paste0("y13867_s3/shiny-logs/brc_formatter/brc_formatter_", current_dt, ".csv")
        # log_tbl <- tibble(Date_Time = current_dt,
        #                   File_Name = input$brc$name,
        #                   File_Size = nrow(out_file),
        #                   Time_to_Complete = time_lapsed)
        # s3write_using(
        #   x = iris,
        #   FUN = write_csv,
        #   bucket = bucket,
        #   object = key
        # )
    })
}
shinyApp(ui, server)