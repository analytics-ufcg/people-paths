library(tidyverse)
library(geosphere)
library(dplyr)
library(magrittr)

#trips_data <- read_csv("/local/juninho/people-paths/R/markdown/2017_07_05_full_agg")

help <- "
Usage:
Rscript trips_data.R <trips_data_filepath> <output-folderpath>
"
## Process args
args <- commandArgs(trailingOnly = TRUE)
min_num_args <- 2
if (length(args) < min_num_args) {
  stop(paste("Wrong number of arguments!", help, sep = "\n"))
}

trips_data_filepath <- args[1]
output_folderpath <- args[2]

#variável que mostra a distância percorrida por cada viagem feita
dist.data <- function(trips_data) {
  x <- 
  trips_data %>% rowwise() %>% 
    mutate(dist = distHaversine(c(from_stop_lon, from_stop_lat), c(to_stop_lon, to_stop_lat)))
}

#variável que mostra o tempo gasto de cada viagem feita
diff.hour <- function(trips_data) {
  x <-
  trips_data %>% 
    mutate(diff_hour = difftime(trips_data$end_time, trips_data$start_time, units = 'hour'))
}

#variável usada para fazer a distribuição da quantidade de viagens das rotas em cada horário do dia
start.time <- function(trips_data) {
  x <- trips_data %>% mutate(start_hour = lubridate::hour(lubridate::ymd_hms(start_time)))
}

end.time <- function(trips_data) {
  x <- trips_data %>% mutate(end_hour = lubridate::hour(lubridate::ymd_hms(start_time)))
}

trips_data <- readr::read_csv(trips_data_filepath)

enhanced_trips_data <- trips_data %>% 
  mutate(trip_duration = round(difftime(trips_data$end_time, trips_data$start_time, units = 'hour') * 60, 0)) %>% 
  mutate(start_hour = lubridate::hour(lubridate::ymd_hms(start_time))) %>% 
  mutate(end_hour = lubridate::hour(lubridate::ymd_hms(start_time))) %>% 
  mutate(date = lubridate::date(lubridate::ymd_hms(start_time))) %>% 
  mutate(week_day = lubridate::wday(date))
  #mutate(dist = distHaversine(c(from_stop_lon, from_stop_lat), c(to_stop_lon, to_stop_lat)))
  

aggregated_trips_data <- enhanced_trips_data %>%
  group_by(date, week_day, route, start_hour, end_hour) %>%
  summarise(quantidade_viagens = n(),
            duration_median = median(trip_duration))


file_name <- tail(stringr::str_split(trips_data_filepath,'/')[[1]], n=1)
readr::write_csv(aggregated_trips_data, paste0(output_folderpath,'/',file_name))




# criar um dataframe agregado com as seguintes colunas: rota, start_time, end_time, número de viagens, mediana da distância, mediana da duração
    #agregar pelas 3 primeiras (de uma vez só) e calcular número de viagens e a mediana pra elas.

# variável bairro da origem e destino (tipo quantas pessoas saem do Centro para bairro x as 10 da manhã)
# quais são as rotas mais populares entre bairros por horário do dia?
    # fazer por proporcionalidade da população do bairro
    # fazer tudo isso por macro região
