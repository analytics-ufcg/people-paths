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
MIN_NUM_ARGS = 9
OD_MATRIX_SUFFIX = '_full_od_trips.csv'
USER_TRIPS_SUFFIX = '_user_trips.csv'
INDEXED_TICKETING_SUFFIX = '_indexed_ticketing.csv'

#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <od_matrix_folderpath> <user_trips_folderpath> <indexed_ticketing_folderpath> <trips_match_folderpath> <od_distribution_folderpath> <dest_missing_trips_folderpath> <initial_date> <final_date>")

def select_input_files(input_folderpath,init_date,fin_date,fname_suffix):
    selected_files = []
    all_files = glob.glob(os.path.join(input_folderpath,"*"))

    for file_ in all_files:
        file_date = pd.to_datetime(file_.split('/')[-1].replace(fname_suffix,''),format='%Y_%m_%d')
        if (file_date >= init_date) and (file_date <= fin_date):
            selected_files.append(file_)

    return sorted(selected_files)

def remove_od_dist_files(od_dist_dir):
    files = glob.glob(os.path.join(od_dist_dir,'*'))
    for f in files:
        os.remove(f)
        

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

od_matrix_folderpath = sys.argv[1]
user_trips_folderpath = sys.argv[2]
indexed_ticketing_folderpath = sys.argv[3]
trips_match_folderpath = sys.argv[4]
od_distribution_folderpath = sys.argv[5]
dest_missing_trips_folderpath = sys.argv[6]
initial_date = sys.argv[7]
final_date = sys.argv[8]


initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

od_matrices = select_input_files(od_matrix_folderpath,initial_date_dt,final_date_dt,OD_MATRIX_SUFFIX)

print("Removing previous OD distribution files...")
remove_od_dist_files(od_distribution_folderpath)

for day_od_mat_filepath in od_matrices:
    od_date_str = day_od_mat_filepath.split('/')[-1].replace(OD_MATRIX_SUFFIX,'')

    print("Processing date: " + od_date_str)

    try:
        #Reading ODMAT Data
        day_od_mat = pd.read_csv(day_od_mat_filepath, parse_dates=['start_time', 'end_time'])

        od_matrix_clean = day_od_mat.filter(['cardNum','user_trip_id','route']) \
                            .rename(index=str, columns={'user_trip_id':'boarding_id','route':'od_route'})

        #Reading User Trips Data
        user_trips_filepath = user_trips_folderpath + os.sep + od_date_str + USER_TRIPS_SUFFIX
        user_trips_data = pd.read_csv(user_trips_filepath, parse_dates=['o_boarding_datetime','o_gps_datetime','next_o_boarding_datetime','next_o_gps_datetime'])
        user_trips_clean = user_trips_data.filter(['cardNum','o_boarding_id','o_route']) \
                                    .rename(index=str, columns={'o_boarding_id':'boarding_id'})
        
        #Reading Ticketing Data
        ticketing_filepath = indexed_ticketing_folderpath + os.sep + od_date_str.replace('_','-') + INDEXED_TICKETING_SUFFIX
        ticketing_data = pd.read_csv(ticketing_filepath, parse_dates=['boarding_datetime'])    
        ticketing_data_clean = ticketing_data.filter(['cardNum','boarding_id','route']) \
                                        .rename(index=str,columns={'route':'t_route'})

        
        #Matching OD Matrices to both User Trips and Ticketing Data
        trips_matches = ticketing_data_clean.merge(od_matrix_clean, how='left', on=['cardNum','boarding_id']) \
                                        .drop_duplicates(['boarding_id']) \
                                        .merge(user_trips_clean, how='left', on=['cardNum','boarding_id'])

        trips_matches = trips_matches.assign(match_level = lambda x: 
                np.where(np.logical_not(np.isnan(x['od_route'])), "fully_matched",
                    np.where(np.logical_and(pd.isna(x.od_route),np.logical_not(pd.isna(x.o_route))), "origin_matched",
                        "unmatched")))

        print("Percentage of trips per match level:")
        print(trips_matches.match_level.value_counts()/len(trips_matches))

        #Adding period of day to data
        period_of_day_dict = {'hour_of_day': [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23], 
                'period_of_day': ['very_late_night','very_late_night','very_late_night','very_late_night','early_morning','early_morning','early_morning','morning','morning','morning','morning','midday','midday','midday','afternoon','afternoon','afternoon','evening','evening','evening','night','night','late_night','late_night']}
        period_of_day_df = pd.DataFrame.from_dict(period_of_day_dict)
        period_of_day_df.period_of_day = period_of_day_df.period_of_day.astype('object', ordered=True)


        #Creating Origin-Destination Distribution dataset
        od_imputation_basis = day_od_mat.filter(['route','busCode','from_stop_id','start_time','to_stop_id','end_time']) \
                                .assign(route = lambda x: x.route.astype(str)) \
                                .assign(hour_of_day = lambda x: x.start_time.dt.hour) \
                                .merge(period_of_day_df, how='inner', on='hour_of_day')
        od_dist = od_imputation_basis.filter(['route','from_stop_id','period_of_day','to_stop_id']) \
                            .sort_values(['route','from_stop_id','period_of_day', 'to_stop_id'])

        #Selecting origin-matched trips for future imputation
        origin_matched_trips = trips_matches.where(lambda x: x.match_level == "origin_matched").merge(user_trips_data, left_on=['cardNum','boarding_id','o_route'], right_on=['cardNum','o_boarding_id','o_route']) \
                                        .assign(start_hour = lambda x: x.o_boarding_datetime.dt.hour)

        origin_matched_trips = origin_matched_trips.filter(['o_boarding_id','o_route','o_boarding_datetime','o_stopPointId']) \
                                                .assign(o_route = lambda x: x.o_route.astype(str)) \
                                                .assign(hour_of_day = lambda x: x.o_boarding_datetime.dt.hour) \
                                                .merge(period_of_day_df, how='inner', on='hour_of_day') \
                                                .drop(['hour_of_day'], axis=1)


        #Writing resulting datasets to file
        trips_matches.to_csv(trips_match_folderpath + os.sep + od_date_str + '_trips_matches.csv', index=False)
        origin_matched_trips.to_csv(dest_missing_trips_folderpath + os.sep + od_date_str + '_dest_missing_trips.csv', index=False)

        day_abrev = pd.to_datetime(od_date_str,format='%Y_%m_%d').strftime("%A")[0:3].lower()
        od_dist_filepath = od_distribution_folderpath + os.sep + day_abrev + '_od_dist.csv'
        first_time = not os.path.isfile(od_dist_filepath)
        with open(od_dist_filepath, 'a') as f:
            od_dist.to_csv(f, header=first_time, index=False)



    except Exception as e:
        print(e)
        print("Skipping date...")
        continue


