library(dplyr)
library(stringr)
library(fuzzyjoin)

bus_operator <- data.frame(
  op_letter = c('B','A','M','C','H','L','J','G','K','E','D'),
  op_desc = c(rep('PONTUAL',4),rep('TRANSBUS',3),rep('PIONEIRO',4)),
  stringsAsFactors = FALSE)

bus_category <- data.frame(
  cat_letter = c('A','B','C','E','L','N','S','T','F','Y'),
  cat_desc = c('Alimentador','Interbairros','Convencional','Expresso','Linha Direta','Circular Centro','Ensino Especial','Turismo','Fretamento Escolar','Veículo Teste'), 
  stringsAsFactors = FALSE)
vehicle_type <- data.frame(
  min_num = c('001','300','500','600','700','850','950'),
  max_num = c('299','499','599','699','849','949','999'),
  type = c('COMUM','PADRON','SEMI PADRON','ARTICULADO','BIARTICULADO','MICRO ESPECIAL','MICRO')
  , stringsAsFactors = FALSE)

na_cats <- data.frame()
na_ops <- data.frame()

files <- list.files(path="/home/tarciso/data/enhanced-buste/", pattern="*_bus_trips.csv", full.names=TRUE, recursive=FALSE)
lapply(files, function(x) {
  enh_buste_data <- read.csv(x)
  
  enh_buste_vehicles <- enh_buste_data %>%
    select(busCode) %>%
    distinct() %>%
    mutate(
      op_letter = str_sub(busCode,1,1),
      cat_letter = str_sub(busCode,2,2),
      bus_num = str_sub(busCode,3,5))
  
  vehicle_carr_cap <-  enh_buste_vehicles %>%
    left_join(bus_operator, by="op_letter") %>%
    left_join(bus_category, by="cat_letter") %>%
    fuzzy_left_join(vehicle_type, 
                    by=c("bus_num" = "min_num",
                         "bus_num" = "max_num"),
                    match_fun = list(`>=`, `<=`))
  
  day_na_cats <- vehicle_carr_cap %>%
    filter(is.na(cat_desc)) %>%
    select(cat_letter)
  
  na_cats <<- rbind(na_cats, day_na_cats) %>% distinct()
  
  day_na_ops <- vehicle_carr_cap %>%
    filter(is.na(op_desc)) %>%
    select(op_letter)
  
  na_ops <<- rbind(na_ops, day_na_ops) %>% distinct()
  
  return()
})



#########################################################################

#Alternative 2

library(jsonlite)

lines_data <- read_json('data/vehicle_data/2017_05_01_linhas.json', simplifyVector = T)

vehicles_data <- read_json('data/vehicle_data/2017_05_01_tabelaVeiculo.json', simplifyVector = T)
