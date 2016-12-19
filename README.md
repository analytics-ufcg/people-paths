# People Paths

People Paths is an application which performs a descriptive analysis on bus GPS and passenger ticketing data, finding paths taken by Public Transportation city users in a time period, and matching the paths origin/destination locations with city zone social data: population, income and literacy rate.

# Data Sources

# Architecture
<div style="display:table-cell; vertical-align:middle; text-align:center">
  <img src="https://drive.google.com/uc?id=0B3NoFHg_3tQrVDBzQVZDT29zZTg" alt="Drawing" width: "180px" height="300px"/>
</div>


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
 * Download Streaming Data files from [owncloud repository](https://bigsea.owncloud.lsd.ufcg.edu.br/owncloud/index.php/s/UFKZhHGdxvWzO8w)
     + doc1 files are ticketing data
     + doc2 files are gps data
 * Unzip json files
 
         gunzip doc*.txt.gz
 * Convert json to csv format
 
         python json2csv.py doc1-file.txt doc1-file.csv file

# Run Analysis (Assuming inside folder with downloaded resource files)
```
Rscript build_trips_locations_social_dataset.R <code.base.folderpath> <ticketing.data.filepath> <gps.data.filepath> metadata/41CURITI.shp 41CURITI metadata/socioeco.csv <output.filepath> <log.filepath>
```
