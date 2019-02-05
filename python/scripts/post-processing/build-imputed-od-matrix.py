#Libraries

#Python Libs
import sys
import os
import glob
import traceback
from datetime import datetime
import time

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 8

DEST_IMPUTED_TRIPS_SUFFIX = '_scaled_od_matrix.csv'
OD_MAT_SUFFIX = '_full_od_trips.csv'
USER_TRIPS_SUFFIX = '_user_trips.csv'
IMPUTED_OD_MATRIX_SUFFIX = '_imputed_od_matrix.csv'


#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <dest_imputed_trips_folderpath> <od_mat_folderpath> <user_trips_folderpath> <gtfs_base_folderpath> <output-folder> <initial_date> <final_date>")

def select_input_files(input_folderpath,init_date,fin_date,fname_suffix):
    selected_files = []
    all_files = glob.glob(os.path.join(input_folderpath,"*"))

    for file_ in all_files:
        file_date = pd.to_datetime(file_.split('/')[-1].replace(fname_suffix,''),format='%Y_%m_%d')
        if (file_date >= init_date) and (file_date <= fin_date):
            selected_files.append(file_)

    return sorted(selected_files)

def get_router_id(query_date):
    INTERMEDIATE_OTP_DATE = pd.to_datetime("2017-06-30", format="%Y-%m-%d")
    router_id = ''

    if (query_date <= INTERMEDIATE_OTP_DATE):
        return 'ctba-2017-1'
    else:
        return 'ctba-2017-2'

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

dest_imputed_trips_folderpath = sys.argv[1]
od_mat_folderpath = sys.argv[2]
user_trips_folderpath = sys.argv[3]
gtfs_base_folderpath = sys.argv[4]
output_folder = sys.argv[5]
initial_date = sys.argv[6]
final_date = sys.argv[7]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

dest_imputed_trips = select_input_files(dest_imputed_trips_folderpath,initial_date_dt,final_date_dt,DEST_IMPUTED_TRIPS_SUFFIX)

for imputed_dest_day_filepath in dest_imputed_trips:
    date_str = imputed_dest_day_filepath.split('/')[-1].replace(DEST_IMPUTED_TRIPS_SUFFIX,'')

    print("Processing date: " + date_str)

    try:
        #Reading Destination Imputed Trips Data
        dest_imputed_trips = pd.read_csv(imputed_dest_day_filepath)

        #Reading Estimated OD Data for the corresponding date
        od_mat_filepath = od_mat_folderpath + os.sep + date_str + OD_MAT_SUFFIX
        od_mat = pd.read_csv(od_mat_filepath, parse_dates=['start_time', 'end_time'])

        od_matrix_clean = od_mat.filter(['cardNum','user_trip_id','start_time','route',
            'from_stop_id','to_stop_id','from_stop_lat','from_stop_lon','to_stop_lat','to_stop_lon']) \
            .rename(index=str, columns={'user_trip_id':'boarding_id','start_time':'boarding_datetime'})

        #Reading User Trips Data for the corresponding date
        user_trips_data_filepath = user_trips_folderpath + os.sep + date_str + USER_TRIPS_SUFFIX
        user_trips_data = pd.read_csv(user_trips_data_filepath, parse_dates=['o_boarding_datetime','o_gps_datetime','next_o_boarding_datetime','next_o_gps_datetime'])

        #Reading Stops data
        router_id = get_router_id(pd.to_datetime(date_str, format="%Y_%m_%d"))
        stops_df = pd.read_csv(gtfs_base_folderpath + os.sep + router_id + os.sep + 'stops.txt')
        stops_metadata = stops_df[['stop_id','stop_lat','stop_lon','parent_station']] \
                .rename(index=str,columns={'stop_id':'stopPointId'}) \
                .drop(['parent_station'], axis=1)

        #Matching imputed stops to their respective geographical coordinates
        user_boardings = user_trips_data.filter(['cardNum','o_boarding_id'])
        expanded_imputed_od = dest_imputed_trips.merge(user_boardings, on=['o_boarding_id']) \
                                        .rename(index=str, columns={'o_boarding_id':'boarding_id',
                                                                   'o_boarding_datetime':'boarding_datetime'}) \
                                        .filter(['cardNum','boarding_id','boarding_datetime','route','from_stop_id','to_stop_id']) \
                                        .merge(stops_metadata, left_on='from_stop_id', right_on='stopPointId') \
                                        .rename(index=str, columns={'stop_lat':'from_stop_lat', 'stop_lon':'from_stop_lon'}) \
                                        .drop('stopPointId', axis=1) \
                                        .merge(stops_metadata, left_on='to_stop_id', right_on='stopPointId') \
                                        .rename(index=str, columns={'stop_lat':'to_stop_lat', 'stop_lon':'to_stop_lon'}) \
                                        .drop('stopPointId', axis=1)

        imputed_od_matrix = pd.concat([od_matrix_clean, expanded_imputed_od]) \
                        .sort_values(['cardNum','boarding_datetime']) \
                        .assign(boarding_datetime = lambda x: pd.to_datetime(x.boarding_datetime, format="%Y-%m-%d %H:%M:%S")) \
                        .rename(index=str, columns={'boarding_id':'trip_id'})

        #Writing final OD Matrix to file
        imputed_od_matrix.to_csv(output_folder + os.sep + date_str + IMPUTED_OD_MATRIX_SUFFIX, index=False)

    except Exception as e:
        print(e)
        print("Skipping date...")
        continue


