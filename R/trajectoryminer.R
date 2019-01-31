#install.packages(c("dplyr","lubridate","stringr","sp","rgeos","rgdal"))

library(dplyr, quietly=T, warn.conflicts=F)
library(lubridate, quietly=T, warn.conflicts=F)
library(stringr, quietly=T, warn.conflicts=F)
library(sp, quietly=T, warn.conflicts=F)
suppressMessages(library(rgeos))
suppressMessages(library(rgdal))

get.trip.interval <- function(timestamp.df) {
  return(difftime(tail(timestamp.df,1), head(timestamp.df,1), units = "hours"))
}

get.trip.distance <- function(longitude.df,latitude.df) {
  return(distGeo(c(tail(longitude.df,1),tail(latitude.df,1)),c(head(longitude.df,1),head(latitude.df,1))))
}

get.group.N.min <- function(time,N) {
  mins.since.midnight <- 60*hour(time) + minute(time)
  return(round(mins.since.midnight/N))
}

prepare.ticketing.data <- function(ticketing.data.filepath) {
  ticketing.data <- read.csv(ticketing.data.filepath, stringsAsFactors = FALSE) %>%
    mutate(codveiculo = CODVEICULO,
           codlinha = CODLINHA,
           numerocartao = NUMEROCARTAO,
           datautilizacao = gsub(",[0-9]+$","",DATAUTILIZACAO),
           nomelinha = NOMELINHA) %>%
    select(codlinha,nomelinha,codveiculo,numerocartao,datautilizacao)
}

prepare.gps.data <- function(gps.data.filepath) {
  gps.data <- read.csv(gps.data.filepath, stringsAsFactors = FALSE) %>%
    mutate(codveiculo = VEIC,
           codlinha = as.character(COD_LINHA),
           latitude = as.numeric(gsub(",",".",LAT)),
           longitude = as.numeric(gsub(",",".",LON)),
           data = DTHR) %>%
    select(codveiculo,latitude,longitude,data,codlinha)
}

build.user.trips.origin.dataset <- function(ticketing.data.filepath,gps.data.filepath,
                                            timestamp.group.size=5,
                                            prep.data=TRUE) {
    if (prep.data) {
        # print("Reading ticketing data...")
        ticketing.data <- prepare.ticketing.data(ticketing.data.filepath)  
        gps.data <- prepare.gps.data(gps.data.filepath)
    } else {
        # print("Reading GPS data...")  
        ticketing.data <- read.csv(ticketing.data.filepath)
        gps.data <- read.csv(gps.data.filepath)
    }
  
    # print("Selecting and Formatting data...")
    # Remocao dos segundos
    ticketing.data$timestamp <- parse_date_time(ticketing.data$datautilizacao, "dmy HMS", tz = "GMT-3")
    ticketing.data$group.5.min <- get.group.N.min(ticketing.data$timestamp, timestamp.group.size)
    
    gps.data$data <- parse_date_time(gps.data$data, "dmy HMS", tz = "GMT-3")
    gps.data$group.5.min <- get.group.N.min(gps.data$data, timestamp.group.size)
  
    ticketing.data <- ticketing.data %>%
        select(codlinha, codveiculo, group.5.min, numerocartao, timestamp) %>%
        arrange(codlinha, codveiculo, group.5.min, timestamp)
  
    gps.data <- gps.data %>%
        group_by(codlinha, codveiculo, group.5.min) %>%
        select(codlinha, codveiculo, latitude, longitude, group.5.min) %>%
        arrange(codlinha, codveiculo, group.5.min) %>%
        filter(row_number() == 1) %>%
        ungroup()
  
    # print("Joining Ticketing and GPS information...")  
    users.trips <- inner_join(ticketing.data, gps.data, 
                            by=c("codlinha","codveiculo","group.5.min")) %>% 
    arrange(numerocartao,timestamp)
    
    users.trips <- users.trips %>% 
        group_by(numerocartao) %>% 
        filter(n() >= 2) 
    
    users.trips <- users.trips[!duplicated(users.trips), ] %>% ungroup()
    
    return(users.trips)
}

add.sector.social.data <- function(trip.zone.data, zones.social.data) {
    social.data <- zones.social.data %>%
    filter(!is.na(CODSETOR) & !is.na(CODSETTX) & !is.na(BA_001) & !is.na(BA_002) & 
             !is.na(BA_003) & !is.na(BA_005) & !is.na(BA_007) & !is.na(BA_009) & 
             !is.na(BA_011) & !is.na(P1_001)) %>%
    mutate(CODSETTX = NULL) %>%
    select(CODSETOR, BA_002, BA_005, P1_001)
    
    colnames(social.data) <- c("cod.setor", "populacao", "renda", "num.alfabetizados")
    
    trip.zone.social.data <- merge(trip.zone.data, social.data, by = "cod.setor") %>%
    select(numerocartao, codlinha, codveiculo, timestamp, cod.setor, nome.bairro,
           cod.bairro, latitude, longitude, populacao, renda, num.alfabetizados)  
}

define.orig.dest.variables <- function(trip.zone.social.data) {
    trip.zone.social.data <- trip.zone.social.data %>% 
        ungroup() %>%
        mutate(date = format(timestamp, "%Y-%m-$d")) %>%
        group_by(numerocartao,date) %>%
        arrange(timestamp) %>%
        mutate(o.sector.code = cod.setor,
               o.neigh.code = cod.bairro,
               o.neigh.name = nome.bairro,
               o.loc = paste(latitude,longitude,sep=","),
               o.timestamp = timestamp,
               o.pop = populacao,
               o.income = renda,
               o.num.literate = num.alfabetizados,
               d.sector.code = lead(cod.setor,default = first(cod.setor)),
               d.neigh.code = lead(cod.bairro,default = first(cod.bairro)),
               d.neigh.name = lead(nome.bairro,default = first(nome.bairro)),
               d.loc = paste(lead(latitude,default=first(latitude)),
                             lead(longitude,default=first(longitude)),sep=","),
               d.timestamp = lead(timestamp,default = first(timestamp)),
               d.pop = lead(populacao,default=first(populacao)),
               d.income = lead(renda,default=first(renda)),
               d.num.literate = lead(num.alfabetizados,default=first(num.alfabetizados))) %>%
        ungroup() %>%
        select(numerocartao,codlinha,
               o.sector.code,o.neigh.code,o.neigh.name,o.loc,o.timestamp,o.pop,o.income,o.num.literate,
               d.sector.code,d.neigh.code,d.neigh.name,d.loc,d.timestamp,d.pop,d.income,d.num.literate)
}

build.user.trips.analysis.dataset <- function(trip.zone.data,zones.social.data) {
  
    #Selecting and renaming useful columns
    trip.zone.data <- trip.zone.data  %>%
        select(codlinha, codveiculo, group.5.min, timestamp, numerocartao, 
               latitude, longitude, CODSETOR, CODBAIRR, NOMEBAIR) %>%
        rename(cod.setor = CODSETOR,
               cod.bairro = CODBAIRR,
               nome.bairro = NOMEBAIR)
  
    #Filtering users with at least 2 trips again, as the sector matching algorithm might have broken some trips
    trip.zone.data <- trip.zone.data %>%
        group_by(numerocartao) %>%
        filter(n() >= 2)
  
    trip.zone.social.data <- add.sector.social.data(trip.zone.data,zones.social.data)
    trip.orig.dest.data <- define.orig.dest.variables(trip.zone.social.data) %>%
        ungroup()
  
    names(trip.orig.dest.data) <- c("card.num","line.code",
                                  "o.sector.code","o.neigh.code","o.neigh.name","o.loc","o.timestamp","o.pop","o.income","o.num.literate",
                                  "d.sector.code","d.neigh.code","d.neigh.name","d.loc","d.timestamp","d.pop","d.income","d.num.literate")
  
    trip.orig.dest.data <- trip.orig.dest.data %>%
        arrange(card.num)
    
    return(trip.orig.dest.data)
}

match.locations.to.city.sectors <- function(zones.shape.data,trips.locations) {
    coordinates(trips.locations) <- ~ longitude + latitude
    proj4string(trips.locations) <- proj4string(zones.shape.data)
    
    locations.zones <- over(trips.locations, zones.shape.data)
    
    matched.locations.zones <- cbind(as.data.frame(trips.locations),locations.zones) %>% 
        filter(!is.na(ID))
    return(matched.locations.zones)
}

read.zones.shape <- function(sectors.shape.filepath,layer.name) {
    readOGR(sectors.shape.filepath, layer = layer.name, verbose=F)
}
