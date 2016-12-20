# People Paths

People Paths is an application which performs a descriptive analysis on bus GPS and passenger ticketing data, finding paths taken by Public Transportation city users in a time period, and matching the paths origin/destination locations with city area social data: population, income and literacy rate.

# Data Sources
 * Bus GPS Data
   + Buses GPS record for a given time period. 
  
 * Bus Ticketing Data
   + Passenger ticketing record for a given time period.
    
 * Census Area Data
   + City census area data with information such as: population, income and literacy rate.
    

# Architecture
<div style="display:table-cell; vertical-align:middle; text-align:center">
  <img src="https://drive.google.com/uc?id=0B3NoFHg_3tQrVDBzQVZDT29zZTg" alt="Drawing" align="center"/>
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

# Run an Analysis
```
Rscript build_trips_locations_social_dataset.R <code.base.folderpath> <ticketing.data.filepath> <gps.data.filepath> metadata/41CURITI.shp 41CURITI metadata/socioeco.csv <output.filepath> <log.filepath>
```

# Sample Input

  * Bus GPS Data
  
    | LATITUDE|   VEHICLE    | LONGITUDE | LINECODE | DATETIME             |
    |:---------:|:-----------------:|:------------:|:--------:| :-------------------------:|
    | -25,351073     | V001 | -49,265108   | A      | 25/06/2016 23:59:57 |
    | -25,35078     | V001 | -49,26514   | A      | 25/06/2016 23:59:47 |
    | -25,350796     | V001 | -49,265528   | A      | 25/06/2016 23:59:40 |   

  * Bus Ticketing Data
  
    | VEHICLECODE|    LINENAME    | CARDNUMBER | LINECODE | TIMESTAMP             |
    |:---------:|:-----------------:|:------------:|:--------:| :-------------------------:|
    | 00239     | LINHA A | 0000000000   | A      | 25/06/16 06:14:03,000000 |
    | 00239     | LINHA B | 0000000001   | B      | 25/06/16 06:28:13,000000 |
    | 00216     | LINHA C | 0000000002   | C      | 25/06/16 08:11:54,000000 |
   
# Sample Output

|card.num|line.code|o.sector.code|o.neigh.code|o.neigh.name|o.loc|o.timestamp|o.pop|o.income|o.num.literate|d.sector.code|d.neigh.code|d.neigh.name|d.loc|d.timestamp|d.pop|d.income|d.num.literate|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|000001|260|410690205040042|410690205033|SAO LOURENCO|"-25.388173,-49.260771"|2016-06-25 19:43:55|833|3268.35|781|410690205040042|410690205033|SAO LOURENCO|"-25.388173,-49.260771"|2016-06-25 19:43:59|833|3268.35|781|
|000002|260|410690205040042|410690205033|SAO LOURENCO|"-25.388173,-49.260771"|2016-06-25 19:43:59|833|3268.35|781|410690205010273|410690205014|AHU|"-25.392713,-49.260928"|2016-06-25 22:03:56|975|4211.39|936|
|000003|260|410690205010273|410690205014|AHU|"-25.392713,-49.260928"|2016-06-25 22:03:56|975|4211.39|936|410690205010273|410690205014|AHU|"-25.392713,-49.260928"|2016-06-25 22:04:01|975|4211.39|936|

   In the output, the column prefix defines whether it refers to the path origin (o.) or destination (d.). Each column is described below:
   
      * card.num: user ticketing card number
      * line.code: bus line code
      * sector.code: city tract to which path origin/destination belongs
      * neigh.code: neighbourhood to which path origin/destination belongs
      * loc: location of path origin/destination
      * timestamp: timestamp when user took the bus/dropped from the bus
      * pop: population of city tract to which path origin/destination belongs
      * income: income of city tract to which path origin/destination belongs
      * num.literate: number of literate people in city tract to which path origin/destination belongs
