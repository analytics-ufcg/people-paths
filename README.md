# People Paths

# Setup Instructions

Tested on a 14.04 Ubuntu machine.

```
echo 'deb http://cran.rstudio.com/bin/linux/ubuntu trusty/'
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
sudo apt-get -y update
sudo apt-get -y upgrade
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

sudo apt-get -y install r-base gunzip
sudo R -e 'install.packages(c("dplyr", "lubridate", "stringr", "sp", "rgeos", "rgdal"), repos = "http://cran.rstudio.com/")'

```

# Prepare Input Files
    * Download files from owncloud repository
        + doc1 files are ticketing data
        + doc2 files are gps data
    * Unzip json files
        `gunzip doc*.txt.gz`
    * Convert json to csv format
        `python json2csv.py doc1-file.txt doc1-file.csv file`

# Run Analysis (Assuming inside folder with downloaded resource files)
```
# Rscript build_trips_locations_social_dataset.R <code.base.folderpath> <ticketing.data.filepath> <gps.data.filepath> metadata/41CURITI.shp 41CURITI metadata/socioeco.csv <output.filepath> <log.filepath>
```
