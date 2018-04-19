#Libraries

#Python Libs
import sys
import os
import glob

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 6
first_cols = ['cardNum', 'boarding_datetime','gps_datetime','route','busCode','stopPointId']
boarding_key_cols = ['cardNum','boarding_datetime']
gps_key_cols = ['route','busCode','tripNum','stopPointId']
sort_cols = boarding_key_cols + gps_key_cols[:-1] + ['gps_datetime']
max_match_diff = 1500

#Functions
def printUsage():
    print "Usage: " + sys.argv[0] + " <buste-base-folder-path> <ticketing-base-folder-path> <output-folder-path> <initial-date> <final-date>"

def readBUSTE_HDFSdir(hdfs_dir_path):
    allFiles = glob.glob(os.path.join(path,"*.csv"))

    frame = pd.DataFrame()
    list_ = []
    for file_ in allFiles:
        df = pd.read_csv(file_, dtype = {'route': str}, na_values='-')
        list_.append(df)
    frame = pd.concat(list_)

    return frame

def select_input_folders(buste_base_path,init_date,fin_date):
    all_folders = glob.glob(os.path.join(buste_base_path,"*"))
    print all_folders
	

#Code
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print "Error: Wrong Usage!"
	printUsage()
        sys.exit(1)

buste_base_folder_path = sys.argv[1]
ticketing_base_folder_pah = sys.argv[2]
output_folder_path = sys.argv[3]
initial_date = sys.argv[4]
final_date = sys.argv[5]	

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

select_input_folders(buste_base_folder_path,initial_date,final_date)


#Reading Boarding Data
#boarding_data = pd.read_csv('/local/tarciso/masters/data/bus_trips/test/doc1-2017_05_10.csv')

sys.exit(0)
