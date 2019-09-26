# people-paths
Socio-spatio-temporal analysis of people movement from bus ticketing data from Curitiba's public bus system.

<h1>Execution Steps<h1>
<h5>Below, we will show all necessary steps for execute the scripts with his necessary parameters.<h5>

### Index Ticketing data

This script turn the ticketing data to structured data with index for each line. This structure is important because the boarding data needs be identificate as unique and the index gives that possibility.

##### Execute the ticketing script: 

index-ticketing-data.py [ticketing-base-folder-path] [output-folder-path] [initial-date] [final-date] 

###### Command example:
```
python index-ticketing-data.py /local/joseiscj/data/ticketing-data/raw/ /local/joseiscj/data/ticketing-data/indexed/ 2017-05-01 2017-07-30
```
### Match GPS points to GTFS trips (BULMA)

##### Execute this example commands: 

```
--class BULMA.MatchingRoutesShapeGPS
```
```
--master spark://10.11.4.10:7077
```
```
--driver-memory 2G
```
```
--executor-memory 2700m
```
Executing with the directories:
```
/home/ubuntu/LQD/BulmaBuste.jar
/user/ubuntu/inputs/shapesCuritiba.csv
/user/ubuntu/inputs/GPS/junho/
/user/ubuntu/outputs/BULMA/ 8
```

### Match Trips to Ticketing data (BUSTE)

##### Execute this example commands: 

```
time /opt/spark/bin/spark-submit 
```
```
--class recordLinkage.BUSTEstimationV3
```
```
--master spark://10.11.4.10:7077
```
```
--driver-memory 2G
```
```
--executor-memory 2700m
```

Executing with the directories:
```
/home/ubuntu/LQD/BulmaBuste.jar
/user/ubuntu/outputs/BULMA-maio/
/user/ubuntu/inputs/shapesCuritiba.csv
/user/ubuntu/inputs/stopsCuritiba.csv
/user/ubuntu/inputs/tickets/
/user/ubuntu/outputs/BUSTE-maio/ 8
```

### Enhance Buste data

This script takes the bus trips and indexed ticketing datas, merge with buste data and makes a improvement in data generated with the merge. The buste script puts in the enhanced data the bus localization and the passenger boarding over time in just one csv file.

##### Execute the BUSTE script: 

enhance-buste-data.py [buste-base-folder-path] [ticketing-base-folder-path] [output-folder-path] [initial-date] [final-date] [terminal-codes-filepath] [gtfs-base-folderpath]

###### Command example:
```
python enhance-buste-data.py /local/joseiscj/data/BUSTE/raw/ /local/joseiscj/data/ticketing-data/indexed/ /local/joseiscj/data/enhanced_buste 2017-04-30 2017-07-30 /local/joseiscj/data/line-000-terminals-translation-table.csv /local/joseiscj/data/gtfs
```
### Split User Trips into parts

##### Execute this example commands: 

```
split -l 200 2017_04_30_user_trips.csv 
```
```
2017_04_30_user_trips_ --numeric-suffixes
```
### Find OTP itinerary alternatives

##### Execute this example commands: 

```
time ls -d /home/ubuntu/otp-n/data/user_trips_parts/2017_07_*.csv
```
```
xargs -n 1 -P 16 -i python /home/ubuntu/otp-n/people-paths/python/scripts/get_otp_itineraries.py {} 
```

Executing with the directories with this server: - http://localhost:10080/otp 
```
/home/ubuntu/otp-n/data/otp_itineraries 
```
### Estimate OD Matrix

##### Execute this example commands: 

```
time ls -d /local/tarciso/data/otp-itineraries/otp_itineraries/2017_05_01_user_trips_1_otp_itineraries.csv
```
```
xargs -n 1 -P 4 -i
```
```
/home/tarciso/anaconda2/bin/python  /local/tarciso/workspace/people-paths/python/scripts/otp-od-builder.py {} 
```

Executing with the directories:
```
/local/tarciso/data/enhanced-buste/user_trips/
/local/tarciso/data/enhanced-buste/bus_trips/
/local/tarciso/data/enhanced-buste/bus_trips/
/local/tarciso/data/od-matrix/
/local/tarciso/experiments/od-estimation/logs/od-estimation-test.txt
```
### Aggregate file parts

##### Execute this example commands: 

```
aggregate-day-files.sh /local/tarciso/masters/data/bus_trips/latest/otp-od/ 
```
```
/local/tarciso/masters/data/bus_trips/latest/otp-od-full/
```
### Prepare OD Matrix Scaling Datasets

##### Executing with the directories: 

```
/local/tarciso/data/od-matrix/full/ 
```
```
/local/tarciso/data/enhanced-buste/user_trips/
```
```
/local/tarciso/data/ticketing/indexed/ 
```
```
/local/tarciso/data/scaled-od-matrix/base-datasets/trips-matches
```
```
/local/tarciso/data/scaled-od-matrix/base-datasets/od-distribution/ 
```
```
/local/tarciso/data/scaled-od-matrix/base-datasets/dest-missing-trips/ 2017-04-30 2017-07-30
```
### Scale OD Matrix (Impute Destinations)

##### Execute this example commands: 

```
python scripts/scale-od-matrix.py 
```

Executing with the directories:
```
/local/tarciso/data/scaled-od-matrix/base-datasets/dest-missing-trips/
/local/tarciso/data/scaled-od-matrix/base-datasets/od-distribution/ 
/local/tarciso/data/scaled-od-matrix/scaled-matrices/ 2017-04-30 2017-07-30
```
### Prepare Vehicle Load Data

##### Execute this example commands: 

```
ls -d /local/tarciso/masters/data/bus_trips/latest/otp-od-full/*
```
```
xargs -n 1 -P 4 -i /local/tarciso/programs/anaconda2/bin/python prepare-model-data.py {} 
```

Executing with the directories:
```
/local/tarciso/masters/data/bus_trips/latest/enhanced-buste/
/local/tarciso/masters/data/bus_trips/latest/vehicle-load/ 
```
### Prepare Model Data

##### Execute this example commands: 

```
spark-submit /local/tarciso/workspace/analytics/btr-spark/src/jobs/data-preprocessing.py 
```

Executing with the directories:
```
/local/tarciso/masters/data/bus_trips/latest/vehicle-load/ 
/local/tarciso/masters/data/bus_trips/latest/model-data/
```
### Train Models

##### Execute this example commands: 

```
 spark-submit /local/tarciso/workspace/analytics/btr-spark/src/jobs/model-training.py
```

Executing with the directories:
```
/local/tarciso/masters/data/bus_trips/latest/model-data/train_data/ 
/local/tarciso/masters/data/bus_trips/latest/model-results/
```
### Model Tunning

