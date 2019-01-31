#Script which prepares data to be show at GEODATA Visualizer tool: http://leasdle01.icei.pucminas.br/geodata/

library(dplyr)
library(lubridate)

input.data <- read.csv("data/trips_locations_28_06_2016.csv")

get.time.from.group.N.min <- function(group.N.min,N) {
  total.mins <- group.N.min * N
  hours <- total.mins / 60
  minutes <- (total.mins / 60) %% 60
  
  return(paste(hours,minutes,"00",sep=":"))
}

group.N.mins.to.timestamp <- function(group.N.mins,N,date) {
  mins <- group.N.mins*N
  days <- floor(mins/1440)
  hours <- floor(mins/60) %% 24
  minutes <- (mins%%60) %% 60
  seconds <- 0
  
  timestamp.str <- paste(date,paste(hours,minutes,seconds,sep=":"))
  
  timestamp <- ymd_hms(timestamp.str,tz = tz(date)) + days(days)
  
  return(format(timestamp,"%H:%M:%S"))
}

geolocated.data <- input.data %>%
  mutate(Name = as.character(codlinha),
         Latitude = latitude,
         Longitude = longitude,
         Date = "06/26/2016",
         Time = group.N.mins.to.timestamp(group.5.min,5,"2016-6-26"),
         Load = 1) %>%
  select(Name, Latitude, Longitude, Date, Time, Load) %>%
  arrange(Time)

write.csv(geolocated.data,"sample-geolocated-data-large.csv",row.names = FALSE)
