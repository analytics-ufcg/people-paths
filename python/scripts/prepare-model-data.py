#Libraries

#Python Libs
import sys
import os

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 4

#Functions
def printUsage():
    print "Usage: " + sys.argv[0] + " <od-trips-filepath> <enhanced-buste-folderpath> <output-folderpath>"

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print "Error: Wrong Usage!"
        printUsage()
        sys.exit(1)

od_trips_filepath = sys.argv[1]
enhanced_buste_folderpath = sys.argv[2]
output_folderpath = sys.argv[3]


file_date_str = od_trips_filepath.split('/')[-1].split('_full_od_trips')[0]
file_date = pd.to_datetime(file_date_str,format='%Y_%m_%d')

print "Processing data for date:", file_date

od_trips = pd.read_csv(od_trips_filepath, parse_dates=['start_time','end_time'])

bus_trips_filepath = enhanced_buste_folderpath + os.sep + file_date_str + '_bus_trips.csv'
bus_trips = pd.read_csv(bus_trips_filepath, dtype={'route': object},parse_dates=['gps_datetime']) \
                .sort_values(['route','busCode','tripNum','gps_datetime']) \
                .assign(route = lambda x: x['route'].astype(str).str.replace("\.0",'').str.zfill(3)) \
                .rename(index=str, columns={'stopPointId':'stop_id'})

boardings_df = od_trips.filter(['route','busCode','tripNum','from_stop_id','start_time']) \
                        .groupby(['route','busCode','tripNum','from_stop_id']) \
                        .count() \
                        .reset_index() \
                        .rename(index=str, columns={'from_stop_id':'stop_id', 'start_time':'boarding_cnt'}) \
                        .sort_values('boarding_cnt', ascending=False)

alightings_df = od_trips.filter(['route','busCode','tripNum','to_stop_id','end_time']) \
                        .groupby(['route','busCode','tripNum','to_stop_id']) \
                        .count() \
                        .reset_index() \
                        .rename(index=str, columns={'to_stop_id':'stop_id', 'end_time':'alighting_cnt'}) \
                        .sort_values('alighting_cnt', ascending=False)

passenger_flows = boardings_df.merge(alightings_df, how='outer') \
                                .sort_values(['boarding_cnt','alighting_cnt']) \
                                .assign(route = lambda x: x['route'].astype(str).str.replace("\.0",'').str.zfill(3),
                                        stop_id = lambda x: x['stop_id'].astype(int))

vehicle_load = bus_trips.merge(passenger_flows, on=['route','busCode','tripNum','stop_id'], how='left') \
                        .assign(boarding_cnt = lambda x: x['boarding_cnt'].fillna(0),
                                alighting_cnt = lambda x: x['alighting_cnt'].fillna(0)) \
                        .assign(crowd_bal = lambda x: x['boarding_cnt'] - x['alighting_cnt']) \
                        .assign(num_pass = lambda x: x.groupby(['route','busCode','tripNum']) \
                                                        .crowd_bal.transform(pd.Series.cumsum))

vehicle_load_output_filepath = output_folderpath + os.sep + file_date_str + '_vehicle_load.csv'
vehicle_load.to_csv(vehicle_load_output_filepath,index=False)
