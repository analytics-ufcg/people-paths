#Libraries

#Python Libs
import sys
import os
import glob

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 7
first_cols = ['cardNum', 'boarding_datetime','gps_datetime','route','busCode','stopPointId']
boarding_key_cols = ['cardNum','boarding_datetime']
gps_key_cols = ['route','busCode','tripNum','stopPointId']
sort_cols = boarding_key_cols + gps_key_cols[:-1] + ['gps_datetime']
max_match_diff = 1800

#Functions
def printUsage():
    print "Usage: " + sys.argv[0] + " <buste-base-folder-path> <ticketing-base-folder-path> <output-folder-path> <initial-date> <final-date> <terminal-codes-filepath>"

def readBUSTE_HDFSdir(path):
    allFiles = glob.glob(os.path.join(path,"*.csv"))

    frame = pd.DataFrame()
    list_ = []
    for file_ in allFiles:
        df = pd.read_csv(file_, dtype = {'route': str}, na_values='-')
        list_.append(df)
    frame = pd.concat(list_)

    return frame

def select_input_folders(buste_base_path,init_date,fin_date):
	selected_folders = []
	all_folders = glob.glob(os.path.join(buste_base_path,"*"))

	for folder in all_folders:
		folder_date = pd.to_datetime(folder.split('/')[-1],format='%Y_%m_%d') 
		if (folder_date >= init_date) and (folder_date <= fin_date):
			selected_folders.append(folder)

	return selected_folders

def get_boarding_data_filepath(buste_date,ticketing_base_path):
	boarding_date = buste_date + pd.DateOffset(days=1)
	boarding_file = ticketing_base_path + os.sep + 'doc1-' + boarding_date.strftime('%Y_%m_%d') + '.csv'

	return boarding_file
	
def check_data_compatibility(buste_df,ticketing_df):
	buste_date = pd.to_datetime(buste_df.at[0,'date'],format='%Y_%m_%d')
	ticketing_date = pd.to_datetime(ticketing_df.at[0,'DATAUTILIZACAO'],format='%d/%m/%y')
	return buste_date == ticketing_date


#Code
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print "Error: Wrong Usage!"
	printUsage()
        sys.exit(1)

buste_base_folder_path = sys.argv[1]
ticketing_base_folder_path = sys.argv[2]
output_folder_path = sys.argv[3]
initial_date = sys.argv[4]
final_date = sys.argv[5]
terminal_codes_file_path = sys.argv[6]	

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

selected_folders = select_input_folders(buste_base_folder_path,initial_date_dt,final_date_dt)

#Reading Boarding Data
for folder in selected_folders:
	folder_date =  pd.to_datetime(folder.split('/')[-1],format='%Y_%m_%d')

	print "Processing date:", folder_date.strftime('%Y-%m-%d')
	#Reading BUSTE Data
	buste_data = readBUSTE_HDFSdir(folder)
	
	#Reading Boarding Data
	boarding_data = pd.read_csv(get_boarding_data_filepath(folder_date,ticketing_base_folder_path))

	#Checking if data matches:
	if not check_data_compatibility(buste_data,boarding_data):
		print "Error: BUSTE and boarding data dates do not match!"
		print "Skipping date..."

	boarding_data['boarding_datetime'] = pd.to_datetime(boarding_data['DATAUTILIZACAO'] + ' ' + boarding_data['HORAUTILIZACAO'],format='%d/%m/%y %H:%M:%S')
	buste_data['gps_datetime'] = pd.to_datetime(buste_data['date'] + ' ' + buste_data['timestamp'],format='%Y_%m_%d %H:%M:%S')
	buste_data['boarding_datetime'] = pd.to_datetime(buste_data['date'] + ' ' + buste_data['cardTimestamp'],format='%Y_%m_%d %H:%M:%S')

	other_cols = [col for col in buste_data.columns if col not in first_cols]
	cols_order = first_cols + other_cols
	gps_by_boarding = buste_data[cols_order].sort_values(boarding_key_cols)


	#Filtering out BUSTE entries whose GPS-Ticketing match time difference is higher than 30 minutes
	gps_by_boarding['match_diff'] = (gps_by_boarding['boarding_datetime'] - gps_by_boarding['gps_datetime']).astype('timedelta64[s]')
	gps_by_boarding_filtered = gps_by_boarding[np.abs(gps_by_boarding['match_diff']) <= max_match_diff]

	num_single_boardings = len(gps_by_boarding.drop_duplicates(subset=boarding_key_cols))
	num_matched_boardings = len(gps_by_boarding_filtered)
	num_missed_boardings = num_single_boardings - num_matched_boardings
	perc_matched_boardings = num_matched_boardings/float(num_single_boardings)
	perc_missed_boardings = num_missed_boardings/float(num_single_boardings)
	#print "single boardings: {}, selected boardings: {} ({}), boardings filtered (large matchdiff) = {} ({})".format(num_single_boardings, num_matched_boardings, perc_matched_boardings, num_missed_boardings, perc_missed_boardings)

	#Build final BUSTE dataset
	
	#GPS with no match / with filtered match
	gps_with_no_match = gps_by_boarding[(np.abs(gps_by_boarding['match_diff']) > max_match_diff) | (pd.isnull(gps_by_boarding['match_diff']))]
	gps_with_no_match.assign(cardNum = np.nan,
							 boarding_datetime = np.nan,
							 birthdate = np.nan,
							 cardTimestamp = np.nan,
							 lineName = np.nan,
							 gender = np.nan)
	#gps_with_no_match.loc[:,['cardNum','boarding_datetime','birthdate','cardTimestamp','lineName','gender']] = np.nan	
	gps_with_no_match_clean = gps_with_no_match.dropna(subset=['route','busCode','tripNum','gps_datetime']) \
                    .drop_duplicates(subset=gps_key_cols)

	#print "GPS w/o match: {}, after removing NAs: {}, Diff: {}".format(len(gps_with_no_match), len(gps_with_no_match_clean), len(gps_with_no_match) - len(gps_with_no_match_clean))

	#Building dataset with unique GPS-Ticketing matches and unique GPS records
	unique_boarding_gps = pd.concat([gps_by_boarding_filtered,gps_with_no_match_clean])
	unique_boarding_gps = unique_boarding_gps[~((unique_boarding_gps.duplicated(subset=gps_key_cols, keep=False)) & (pd.isnull(unique_boarding_gps['cardNum'])))].sort_values(sort_cols)
	
	# Match station/terminal boarding registries with their respective stop codes
	terminal_codes = pd.read_csv(terminal_codes_file_path, dtype = {'URBS_CODE': str})

	matched_station_boarding = boarding_data.merge(terminal_codes, left_on='CODVEICULO', right_on='URBS_CODE', how='inner').sort_values(by='DATAUTILIZACAO')
	num_matched_stations = len(matched_station_boarding)
	total_station_boarding = len(boarding_data[boarding_data.CODVEICULO.str.isnumeric()])
	#print num_matched_stations, total_station_boarding, num_matched_stations/float(total_station_boarding)

	#Formatting stations boarding data to fit BUSTE data format
	terminal_boardings = matched_station_boarding.drop(['LINE','NAME','URBS_CODE','LAT','LON','DATAUTILIZACAO'], axis=1).rename(index=str, columns={'CODLINHA': 'route', 'CODVEICULO': 'busCode', 
                                                    'DATANASCIMENTO':'birthdate',
                                                    'HORAUTILIZACAO':'cardTimestamp',
                                                    'NOMELINHA':'lineName',
                                                    'NUMEROCARTAO':'cardNum',
                                                    'SEXO':'gender',
                                                    'STOP_ID':'stopPointId'})

	gps_boardings_with_terminals = pd.concat([unique_boarding_gps,terminal_boardings], ignore_index=True)
	gps_boardings_with_terminals = gps_boardings_with_terminals[['cardNum', 'boarding_datetime', 'route', 'busCode', 'tripNum', 'gps_datetime','stopPointId',
                                      'shapeId','shapeSequence','shapeLat','shapeLon','distanceTraveledShape','problem','lineName','birthdate','gender']].sort_values(sort_cols)

	gps_boardings_with_terminals.to_csv(output_folder_path + os.sep + folder_date.strftime('%Y_%m_%d')  + '.csv', index=False)
	
print "Finishing Script..."

sys.exit(0)
