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
MIN_NUM_ARGS = 6
SEED = 199

DEST_MISSING_TRIPS_SUFFIX = '_dest_missing_trips.csv'
OD_DIST_SUFFIX = '_od_dist.csv'
SCALED_ODMAT_SUFFIX = '_scaled_od_matrix.csv'


#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <dest_missing_trips_folderpath> <od_distribution_folderpath> <output-folder> <initial_date> <final_date>")

def select_input_files(input_folderpath,init_date,fin_date,fname_suffix):
    selected_files = []
    all_files = glob.glob(os.path.join(input_folderpath,"*"))

    for file_ in all_files:
        file_date = pd.to_datetime(file_.split('/')[-1].replace(fname_suffix,''),format='%Y_%m_%d')
        if (file_date >= init_date) and (file_date <= fin_date):
            selected_files.append(file_)

    return sorted(selected_files)

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

dest_missing_trips_folderpath = sys.argv[1]
od_distribution_folderpath = sys.argv[2]
output_folder = sys.argv[3]
initial_date = sys.argv[4]
final_date = sys.argv[5]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

dest_missing_trips = select_input_files(dest_missing_trips_folderpath,initial_date_dt,final_date_dt,DEST_MISSING_TRIPS_SUFFIX)

for missing_dest_day_filepath in dest_missing_trips:
    date_str = missing_dest_day_filepath.split('/')[-1].replace(DEST_MISSING_TRIPS_SUFFIX,'')

    print("Processing date: " + date_str)

    try:
        #Reading Origin-Matched Data
        origin_matched = pd.read_csv(missing_dest_day_filepath, parse_dates=['o_boarding_datetime']) \
                            .drop(['period_of_day'],axis=1)

        #Reading OD Distribution Data for the corresponding weekday
        weekday = pd.to_datetime(date_str,format='%Y_%m_%d').strftime("%A")[0:3].lower()
        od_dist_filepath = od_distribution_folderpath + os.sep + weekday + OD_DIST_SUFFIX
        od_dist_weekday = pd.read_csv(od_dist_filepath,
                                        dtype={'route': str,
                                               'from_stop_id': np.float64,
                                               'period_of_day': str,
                                               'to_stop_id': np.float64}) \
                            .drop(['period_of_day'],axis=1)

        #Random Sampling from OD Destination Distribution
        inference_alternatives = origin_matched.merge(od_dist_weekday, left_on=['o_route','o_stopPointId'], right_on=['route','from_stop_id'])

        scaled_od_matrix = inference_alternatives.groupby(['o_boarding_id']) \
                        .apply(lambda x: x.sample(1, random_state=SEED)) \
                        .reset_index(drop=True)

        #Writing resulting datasets to file
        scaled_od_matrix.to_csv(output_folder + os.sep + date_str + SCALED_ODMAT_SUFFIX, index=False)

    except Exception as e:
        print(e)
        print("Skipping date...")
        continue


