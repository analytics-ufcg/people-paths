#Libraries

#Python Libs
import sys
import os
import glob
from datetime import datetime
import time

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 7

#Functions
def printUsage():
    print "Usage: " + sys.argv[0] + " <enhanced-buste-folderpath> <otp-suggestions-folderpath>  <gtfs-base-folderpath> <output-folderpath> <initial-date> <final-date>"

def select_input_files(enh_buste_base_path,init_date,fin_date,suffix):
	selected_files = []
	all_files = glob.glob(os.path.join(enh_buste_base_path,"*"))

	for file_ in all_files:
		try:
			file_date = pd.to_datetime(file_.split('/')[-1],format=('%Y_%m_%d' + suffix  + '.csv'))
			if (file_date >= init_date) and (file_date <= fin_date):
				selected_files.append((file_,file_date))
		except:
			continue	

	return sorted(selected_files)

def dist(stop_lat, stop_lon,next_o_lat,next_o_lon):
    return np.arccos(
        np.sin(np.radians(stop_lat)) * np.sin(np.radians(next_o_lat)) + 
        np.cos(np.radians(stop_lat)) * np.cos(np.radians(next_o_lat)) * 
            np.cos(np.radians(stop_lon) - np.radians(next_o_lon))
    ) * 6371

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
        print "Error: Wrong Usage!"
        printUsage()
        sys.exit(1)

enhanced_buste_folderpath = sys.argv[1]
otp_suggestions_folderpath = sys.argv[2]
gtfs_base_folderpath = sys.argv[3]
output_folderpath = sys.argv[4]
initial_date = sys.argv[5]
final_date = sys.argv[6]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

selected_files = select_input_files(enhanced_buste_folderpath,initial_date_dt,final_date_dt,'_user_trips')

for file_,file_date in selected_files:
	file_date_str = file_date.strftime('%Y_%m_%d')
	print "Processing date", file_date_str

	# Read Origin/Next-Origin Pairs
	trips_origins_filepath = file_
	trips_origins = pd.read_csv(trips_origins_filepath, parse_dates=['o_boarding_datetime','o_gps_datetime','next_o_boarding_datetime','next_o_gps_datetime'])

	# Filter Origin/Next-Origin Pairs
	trips_origins['dist_between_origins'] = trips_origins.apply(lambda x: dist(x['o_stop_lat'],x['o_stop_lon'],x['next_o_stop_lat'],x['next_o_stop_lon']), axis=1)
	trips_origins['boardings_timediff'] = pd.to_timedelta(trips_origins['boardings_timediff'])	

	trips_origins['boardings_timediff'] = np.where(np.isnat(trips_origins['boardings_timediff']),
                                             trips_origins['o_boarding_datetime'] - trips_origins['next_o_boarding_datetime'],
                                             trips_origins['boardings_timediff'])

	trips_origins_clean = trips_origins[(trips_origins['dist_between_origins'] > 1.5) &
                                    (trips_origins['boardings_timediff'] > pd.Timedelta('5 min'))]

	# Read OTP Suggestions
	otp_suggestions_filepath = otp_suggestions_folderpath + os.sep + file_date_str + '_otp_itineraries.csv'
	otp_suggestions = pd.read_csv(otp_suggestions_filepath, parse_dates=['date','otp_start_time','otp_end_time'])
	
	#Prepare OTP data for analysis
	otp_suggestions['otp_start_time'] = otp_suggestions['otp_start_time'] - pd.Timedelta('10800 s')
	otp_suggestions['otp_end_time'] = otp_suggestions['otp_end_time'] - pd.Timedelta('10800 s')
	otp_suggestions['route'] = otp_suggestions['route'].astype(str)
	otp_suggestions['route'] = np.where(otp_suggestions['mode'] == 'BUS',
                                    otp_suggestions['route'].astype(str).str.replace("\.0",'').str.zfill(3),
                                    otp_suggestions['route'])
	
	otp_date = otp_suggestions['date'][0]
	ticketing_date = pd.to_datetime(trips_origins['o_boarding_datetime'].dt.strftime('%Y-%m-%d')[0])

	if (otp_date != ticketing_date):
		print "ERROR: OTP date", otp_date, "does not match Ticketing data", ticketing_date
		print "Skipping current day"
		continue
	
	
	# Adding Parent Stop data to OTP Suggestions
	router_id = get_router_id(otp_date)
	stops_filepath = gtfs_base_folderpath + os.sep + router_id + os.sep + 'stops.txt'
	stops_df = pd.read_csv(stops_filepath)
	stops_parent_stations = stops_df[['stop_id','parent_station']]
	otp_suggestions = otp_suggestions.merge(stops_parent_stations, left_on='from_stop_id', right_on='stop_id', how='left') \
                                    .drop(['stop_id'], axis=1)
	
	# Selecting trips for whom OTP suggestions were found
	selected_trips = trips_origins_clean[trips_origins_clean['o_boarding_id'].isin(otp_suggestions['user_trip_id'])]

	# Matching all kinds of boarding events to valid OTP suggestions
	itineraries_start = otp_suggestions.query('mode == \'BUS\'') \
                    .groupby(['user_trip_id','itinerary_id']) \
                    .first() \
                    .reset_index()

	# Matching vehicle boarding origins
	vehicle_boarding_origins = selected_trips[np.logical_not(selected_trips['o_busCode'].str.isdigit())]
	matched_vehicle_boardings = vehicle_boarding_origins.merge(itineraries_start, left_on=['o_boarding_id','o_route','o_stopPointId'], right_on=['user_trip_id','route','from_stop_id'], how='inner')
	num_matched_vehicle_boardings = len(matched_vehicle_boardings.drop_duplicates(subset=['cardNum','o_boarding_id']))

	print "Vehicle boardings with matching OTP suggestions: ", num_matched_vehicle_boardings, "(", \
                                                            100*(num_matched_vehicle_boardings/float(len(vehicle_boarding_origins))), "%)"

	# Matching terminal boarding origins
	terminal_boarding_origins = selected_trips[selected_trips['o_busCode'].str.isdigit()]

	terminal_boarding_origins = selected_trips[(selected_trips['o_busCode'].str.isdigit()) & (selected_trips['o_route'] != '021')]

	matched_terminal_boardings = terminal_boarding_origins.merge(itineraries_start, left_on=['o_boarding_id','o_stopPointId'], right_on=['user_trip_id','parent_station'], how='inner') \
                .drop_duplicates(subset=['cardNum','o_boarding_id'])

	num_matched_terminal_boardings = len(matched_terminal_boardings.drop_duplicates(subset=['cardNum','o_boarding_id']))

	print "Terminal boardings with matching OTP suggestions: ", num_matched_terminal_boardings, "(", \
                                                            100*(num_matched_terminal_boardings/float(len(terminal_boarding_origins))), "%)"

	# Matching special case route 021 terminal boarding origins 
	terminal_021_origins = selected_trips[(selected_trips['o_busCode'].str.isdigit()) & (selected_trips['o_route'] == '021')]
	matched_021_terminal_boardings = terminal_021_origins.merge(itineraries_start, left_on=['o_boarding_id','o_route','o_stopPointId'], right_on=['user_trip_id','route','parent_station'], how='inner')	
	num_matched_021_terminal_boardings = len(matched_021_terminal_boardings.drop_duplicates(subset=['cardNum','o_boarding_id']))

	print "Line 021 Terminal boardings with matching OTP suggestions: ", num_matched_021_terminal_boardings, "(", \
                                                            100*(num_matched_021_terminal_boardings/float(len(terminal_021_origins))), "%)"
	
	total_num_matches = num_matched_vehicle_boardings + num_matched_021_terminal_boardings + num_matched_terminal_boardings

	print "Total number of matches: ", total_num_matches, "(", \
                                    100*(total_num_matches/float(len(selected_trips))), "%)"

	boarding_suggestions_matches = pd.concat([matched_vehicle_boardings,matched_021_terminal_boardings,matched_terminal_boardings])

	# Add OTP extra origin/next-origin pairs to final dataset
	otp_legs_suggestions_matches = boarding_suggestions_matches[np.append(trips_origins_clean.columns.values,['itinerary_id'])] \
                    .merge(otp_suggestions, left_on=['o_boarding_id','itinerary_id'], right_on=['user_trip_id','itinerary_id'], how='inner') \
                    .query('mode == \'BUS\'')

	otp_legs_suggestions_matches['first_vehicle_boarding'] = np.where(np.logical_not(otp_legs_suggestions_matches['o_busCode'].str.isdigit()) & 
                                                                      (otp_legs_suggestions_matches['o_route'] == otp_legs_suggestions_matches['route']),
                                                                      True,
                                                                      False)

	otp_filtered_legs = otp_legs_suggestions_matches[np.append(otp_suggestions.columns.values,['first_vehicle_boarding','o_busCode','o_tripNum','o_boarding_datetime'])]


	# Find OTP Suggested Itineraries in BUSTE Data
	bus_trips_filepath = enhanced_buste_folderpath + os.sep + file_date_str + '_bus_trips.csv'
	bus_trips = pd.read_csv(bus_trips_filepath, dtype={'route': object},parse_dates=['gps_datetime'])
	
	bus_trips = bus_trips.sort_values(['route','busCode','tripNum','gps_datetime'])
	bus_trips['route'] = bus_trips['route'].astype(str).str.replace("\.0",'').str.zfill(3)
	
	# Find legs start point
	otp_legs_buste_start = otp_filtered_legs.merge(bus_trips, 
                                 left_on=['route','from_stop_id'], 
                                 right_on=['route','stopPointId'], 
                                 how='inner') \
                        .assign(otp_buste_start_timediff = lambda x: np.absolute(x['gps_datetime'] - x['otp_start_time'])) \
                        .sort_values(['user_trip_id','itinerary_id','leg_id','otp_buste_start_timediff']) \
                        .groupby(['user_trip_id','itinerary_id','leg_id']) \
                        .first() \
                        .reset_index() \
                        .loc[:, ['user_trip_id','first_vehicle_boarding','itinerary_id','leg_id','route','busCode','o_busCode','tripNum','o_tripNum','from_stop_id','otp_start_time','gps_datetime','o_boarding_datetime','otp_buste_start_timediff','to_stop_id','otp_end_time']]

	# Find legs end point
	otp_legs_buste = otp_legs_buste_start \
                        .rename(index=str, columns={'to_stop_id':'stopPointId', 'gps_datetime':'matched_start_time'}) \
                        .merge(bus_trips, 
                                 on=['route','busCode','tripNum','stopPointId'], 
                                 how='inner') \
                        .assign(otp_buste_end_timediff = lambda x: np.absolute(x['gps_datetime'] - x['otp_end_time'])) \
                        .sort_values(['user_trip_id','itinerary_id','leg_id','otp_buste_end_timediff']) \
                        .groupby(['user_trip_id','itinerary_id','leg_id']) \
                        .first() \
                        .reset_index() \
                        .rename(index=str, columns={'stopPointId':'to_stop_id', 'gps_datetime':'matched_end_time'}) \
                        .assign(leg_duration = lambda x: x['matched_end_time'] - x['matched_start_time'],
                                boarding_otp_match_start_timediff = lambda x: np.absolute(x['o_boarding_datetime'] - x['matched_start_time'])) \
                        .loc[:, ['user_trip_id','first_vehicle_boarding','itinerary_id','leg_id','route','busCode','o_busCode','tripNum','o_tripNum','from_stop_id','otp_start_time','matched_start_time','o_boarding_datetime','otp_buste_start_timediff','to_stop_id','otp_end_time','matched_end_time','otp_buste_end_timediff', 'boarding_otp_match_start_timediff', 'leg_duration']]
                        
	
	# Choosing itinerary
	# Adding stops location data

	stops_locations = stops_df[['stop_id','stop_lat','stop_lon']]
	user_trips_ids = otp_legs_suggestions_matches[['cardNum','user_trip_id']].drop_duplicates().sort_values(['cardNum','user_trip_id'])
	otp_legs_buste_data = otp_legs_buste.merge(stops_locations, left_on='from_stop_id', right_on='stop_id', how='left') \
        .drop('stop_id', axis=1) \
        .rename(index=str, columns={'stop_lat':'from_stop_lat','stop_lon':'from_stop_lon'}) \
        .merge(stops_locations, left_on='to_stop_id', right_on='stop_id', how='left') \
        .drop('stop_id', axis=1) \
        .rename(index=str, columns={'stop_lat':'to_stop_lat','stop_lon':'to_stop_lon'}) \
        .merge(user_trips_ids, on=['user_trip_id'], how='inner') \
                            [np.append(np.append(['cardNum'],otp_legs_buste.columns.values),['from_stop_lat','from_stop_lon','to_stop_lat','to_stop_lon'])]

	# Summarizing suggested itineraries information
	otp_buste_itineraries = otp_legs_buste_data \
                            .groupby(['cardNum','user_trip_id','itinerary_id']) \
                            .agg({'from_stop_id': lambda x: x.iloc[0], 
                                  'matched_start_time': lambda x: x.iloc[0], 
                                  'from_stop_lat': lambda x: x.iloc[0], 
                                  'from_stop_lon': lambda x: x.iloc[0],
                                  'to_stop_id': lambda x: x.iloc[-1], 
                                  'matched_end_time': lambda x: x.iloc[-1], 
                                  'to_stop_lat': lambda x: x.iloc[-1], 
                                  'to_stop_lon': lambda x: x.iloc[-1],
                                  'leg_id': lambda x: len(x),
                                  'first_vehicle_boarding' : lambda x: x.any()}) \
                            .rename(index=str, columns={'leg_id':'num_transfers','first_vehicle_boarding':'vehicle_boarding'}) \
                            .add_prefix('match_') \
                            .reset_index() \
                            .assign(cardNum = lambda x: x['cardNum'].astype(float),
                                    user_trip_id = lambda x: x['user_trip_id'].astype(int),
                                    itinerary_id = lambda x: x['itinerary_id'].astype(int))

	otp_buste_itineraries_summary = otp_buste_itineraries \
                            .merge(otp_legs_suggestions_matches.drop_duplicates(subset=['cardNum','user_trip_id','itinerary_id']), on=['cardNum','user_trip_id','itinerary_id'], how='inner') \
                            [['cardNum', 'user_trip_id', 'itinerary_id',
                                  'match_from_stop_id', 'match_matched_start_time', 'o_boarding_datetime',
                                  'match_from_stop_lat', 'match_from_stop_lon', 'o_stop_lat', 'o_stop_lon',
                                  'match_to_stop_id', 'match_matched_end_time', 'next_o_boarding_datetime',
                                  'match_to_stop_lat', 'match_to_stop_lon', 'next_o_stop_lat', 'next_o_stop_lon','match_num_transfers', 'match_vehicle_boarding']] \
                            .assign(start_diff = lambda x: np.absolute(x['match_matched_start_time'] - x['o_boarding_datetime']),
                                    trip_duration = lambda x: x['match_matched_end_time'] - x['match_matched_start_time'],
                                    origin_dist = lambda x: dist(x['match_from_stop_lat'], x['match_from_stop_lon'], x['o_stop_lat'], x['o_stop_lon']),
                                    next_origin_dist = lambda x: dist(x['match_to_stop_lat'], x['match_to_stop_lon'], x['next_o_stop_lat'], x['next_o_stop_lon'])) \
                            .sort_values(['cardNum','user_trip_id'])

	otp_buste_itineraries_filtered = otp_buste_itineraries_summary[((otp_buste_itineraries_summary['trip_duration'] > pd.Timedelta('0s')) & (otp_buste_itineraries_summary['trip_duration'] < pd.Timedelta('2h'))) &
                                                               ((otp_buste_itineraries_summary['start_diff'] > pd.Timedelta('0s')) & (otp_buste_itineraries_summary['start_diff'] < pd.Timedelta('1.5h')))] \
                                    .query('origin_dist < 0.1') \
                                    .query('next_origin_dist < 2.0')

	# Assigning suggested itineraries a penalty score

	otp_buste_itineraries_penalty = otp_buste_itineraries_filtered \
                                    .assign(penalty = lambda x: 2*x['start_diff'].dt.total_seconds() + x['trip_duration'].dt.total_seconds() + x['match_num_transfers']*10) \
                                    [['cardNum','user_trip_id','itinerary_id','match_num_transfers','match_vehicle_boarding','next_origin_dist','origin_dist','start_diff','trip_duration','penalty']] \
                                    .sort_values(['user_trip_id','penalty'], ascending=True)

	# Choose best itineraries based on the penalty score
	chosen_itineraries = otp_buste_itineraries_penalty.groupby(['user_trip_id']).first().reset_index()

	# Filtering chosen itineraries
	chosen_itineraries = chosen_itineraries[(np.logical_not(chosen_itineraries['match_vehicle_boarding'])) | ((chosen_itineraries['match_vehicle_boarding']) & (chosen_itineraries['start_diff'] < pd.Timedelta('20 min')))]

	# Building final Origin-Destination Trips dataframe
	od_trips = chosen_itineraries.merge(otp_legs_buste_data, on=['cardNum','user_trip_id','itinerary_id'], how='inner') \
        [['cardNum','user_trip_id','itinerary_id','leg_id','route','busCode','tripNum','from_stop_id','matched_start_time','from_stop_lat','from_stop_lon','to_stop_id','matched_end_time','to_stop_lat','to_stop_lon','leg_duration']] \
        .rename(index=str, columns={'matched_start_time':'start_time','matched_end_time':'end_time'})

	# Writing final OD Trips dataset to file
	od_trips.to_csv(output_folderpath + os.sep + file_date_str + '_od_trips.csv',index=False)

