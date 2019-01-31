#!/usr/bin/env Rscript
args = commandArgs(trailingOnly = TRUE)

write.log <- function(log.text, filename) {
  log.text <- paste(Sys.time(), log.text, sep = " - ")
  write(log.text, file = filename, append = TRUE)
}

MIN_NUM_ARGS = 8

if (length(args) < MIN_NUM_ARGS) {
    stop(paste("Wrong number of arguments!",
               "Usage: Rscript build_trips_locations_social_dataset.R <code.base.folderpath> <ticketing.data.filepath> <gps.data.filepath> <city.zone.shape.filepath> <city.zone.shape.layer.name> <trip.zone.data.filepath> <output.filepath> <log.filepath>",sep="\n"))
}

path.finder.base.folderpath = args[1]
ticketing.data.filepath = args[2]
gps.data.filepath = args[3]
city.zone.shape.filename = args[4]
city.zone.shape.layer.name = args[5]
trip.zone.data.filename = args[6]
output.filepath = args[7]
log.filepath = args[8]
city.zone.shape.filepath = paste(path.finder.base.folderpath, city.zone.shape.filename, sep = "/")
trip.zone.data.filepath = paste(path.finder.base.folderpath, trip.zone.data.filename, sep = "/")

write.log(log.text = "=== Starting Path Finder LOG ===", filename = log.filepath)
write.log(log.text = "1/6 - Loading libs...", filename = log.filepath)
source(paste(path.finder.base.folderpath, "trajectoryminer.R", sep = "/"))

proc.time <- system.time({
    
    write.log(log.text = "2/6 - Reading social/geographical metadata...", filename = log.filepath)
    social.data <- read.csv2(trip.zone.data.filepath)
    zones.shape.data <- read.zones.shape(city.zone.shape.filepath,city.zone.shape.layer.name)

    write.log(log.text = "3/6 - Finding trips locations...", filename = log.filepath)
    trip.locations <- build.user.trips.origin.dataset(ticketing.data.filepath,gps.data.filepath)
    
    write.log(log.text = "4/6 - Matching trips locations to city zones...", filename = log.filepath)
    locations.sectors.match <- match.locations.to.city.sectors(zones.shape.data,
                                                               trip.locations)
    write.log(log.text = "5/6 - Adding social data information...", filename = log.filepath)
    trip.zone.social.data <- build.user.trips.analysis.dataset(locations.sectors.match,social.data)
    
    write.log(log.text = "6/6 - Writing results to file...", filename = log.filepath)
    write.csv(trip.zone.social.data,output.filepath,row.names = FALSE)

})

write.log(log.text = paste("Processing Time:",proc.time[3]), filename = log.filepath)
write.log(log.text = "=== Finishing Path Finder LOG ===", filename = log.filepath)
