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

wget "https://drive.google.com/uc?export=download&id=0B1Gus4pWNSP2YWVIMEVxN1pqTDA" -O socioeco.csv
wget "https://drive.google.com/uc?export=download&id=0B1Gus4pWNSP2a0FTbTdXTjF6LVk" -O 41cutiriba.zip
unzip 41curitiba.zip

```

# Prepare Input Files
    * Download files from owncloud repository
        + doc1 files are ticketing data
        + doc2 files are gps data
    * Unzip json files
        `gunzip doc*.txt.gz`
    * Convert json to csv format
        `python /path/to/project/folder/scripts/json2csv.py doc1-file.txt doc1-file.csv file`

# Run Analysis (Assuming inside folder with downloaded resource files)
```
# Rscript /path/to/project/folder/demo_bh/build_trips_locations_social_dataset.R <ticketing.data.filepath> <gps.data.filepath> 41CURITI.shp 41CURITI socioeco.csv <output.filepath>
```
