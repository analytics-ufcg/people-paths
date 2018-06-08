#Libraries

#Python Libs
import sys
import os
import glob
from datetime import datetime
import time
from geopy import distance


#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 5

#Functions
def printUsage():
    print "Usage: " + sys.argv[0] + " <otp-suggestions-filepath> <enhanced-buste-folderpath> <gtfs-base-folderpath> <output-folderpath>"

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

def dist(p1_lat, p1_lon, p2_lat, p2_lon):
    return np.around(distance.geodesic((p1_lat,p1_lon),(p2_lat,p2_lon)).km,decimals=5)

def get_router_id(query_date):
    INTERMEDIATE_OTP_DATE = pd.to_datetime("2017-06-30", format="%Y-%m-%d")
    router_id = ''

    if (query_date <= INTERMEDIATE_OTP_DATE):
        return 'ctba-2017-1'
    else:
        return 'ctba-2017-2'

def choose_leg_matches(leg_matches_groups):
	chosen_leg_matches = pd.DataFrame(columns = otp_legs_buste.columns.values)
	prev_group_id = ()
	num_groups_not_survived = 0

	for name, group in legs_matches_groups:
			
		if (prev_group_id != name[0:2]):
			prev_leg_end_time = otp_suggestions['date'][0]
		
		#print
		#print prev_leg_end_time
		#print
		#print "Original Group"
		#print group.filter(['otp_start_time','matched_start_time'])
			
		filtered_group = group[group['matched_start_time'] > prev_leg_end_time]
		#print
		#print "Filtered Group"
		#print filtered_group.filter(['otp_start_time','matched_start_time'])
			
		if (len(filtered_group) == 0):
			num_groups_not_survived += 1
			continue
			
		chosen_leg_match = filtered_group.sort_values('boarding_otp_match_start_timediff').iloc[0]
		#print "Chosen Leg"
		#print chosen_leg_match
			
		chosen_leg_matches = chosen_leg_matches.append(chosen_leg_match)
			
		#Update variables
		prev_group_id = name[0:2]
		prev_leg_end_time = chosen_leg_match['matched_end_time']


	#print num_groups_not_survived
	return chosen_leg_matches.filter(otp_legs_buste.columns.values)

def prepare_otp_data(otp_data):
	otp_data['otp_start_time'] = otp_data['otp_start_time'] - pd.Timedelta('10800 s')
	otp_data['otp_end_time'] = otp_data['otp_end_time'] - pd.Timedelta('10800 s')
	otp_data['route'] = otp_data['route'].astype(str)
	otp_data['route'] = np.where(otp_data['mode'] == 'BUS',
                            otp_data['route'].astype(str).str.replace("\.0",'').str.zfill(3),
                            otp_data['route'])

	return otp_data

def match_vehicle_boardings(selected_trips,itineraries_start):
	vehicle_boarding_origins = selected_trips[np.logical_not(selected_trips['o_busCode'].str.isdigit())]
	matched_vehicle_boardings = vehicle_boarding_origins.merge(itineraries_start, left_on=['o_boarding_id','o_route','o_stopPointId'], right_on=['user_trip_id','route','from_stop_id'], how='inner')
	num_matched_vehicle_boardings = len(matched_vehicle_boardings.drop_duplicates(subset=['cardNum','o_boarding_id']))
	match_perc = 100*(num_matched_vehicle_boardings/float(len(vehicle_boarding_origins)))
	return (matched_vehicle_boardings,num_matched_vehicle_boardings,match_perc)

def compatible_dates(otp_data,ticketing_data):
	otp_date = otp_data['date'].iloc[0]
	ticketing_date = pd.to_datetime(ticketing_data['o_boarding_datetime'].dt.strftime('%Y-%m-%d')[0])

	return (otp_date == ticketing_date,otp_date,ticketing_date)

def match_terminal_boardings(selected_trips,itineraries_start):
	terminal_boarding_origins = selected_trips[(selected_trips['o_busCode'].str.isdigit()) & (selected_trips['o_route'] != '021')]
	matched_terminal_boardings = terminal_boarding_origins.merge(itineraries_start, 
																left_on=['o_boarding_id','o_stopPointId'], 
																right_on=['user_trip_id','parent_station'], how='inner')
	num_matched_terminal_boardings = len(matched_terminal_boardings.drop_duplicates(subset=['cardNum','o_boarding_id']))
	matched_perc = 100*(num_matched_terminal_boardings/float(len(terminal_boarding_origins)))
	return (matched_terminal_boardings,num_matched_terminal_boardings,matched_perc)

def match_terminal_021_boardings(selected_trips,itineraries_start):
	terminal_021_origins = selected_trips[(selected_trips['o_busCode'].str.isdigit()) & (selected_trips['o_route'] == '021')]
	matched_021_terminal_boardings = terminal_021_origins.merge(itineraries_start, left_on=['o_boarding_id','o_route','o_stopPointId'], right_on=['user_trip_id','route','parent_station'], how='inner')	
	num_matched_021_terminal_boardings = len(matched_021_terminal_boardings.drop_duplicates(subset=['cardNum','o_boarding_id']))
	terminal_021_match_perc = 100*(num_matched_021_terminal_boardings/float(len(terminal_021_origins)))
	return (len(terminal_021_origins),matched_021_terminal_boardings,num_matched_021_terminal_boardings,terminal_021_match_perc)

def get_otp_matched_legs(boarding_suggestions_matches,otp_suggestions):
	otp_legs_suggestions_matches = boarding_suggestions_matches \
									.filter(np.append(trips_origins.columns.values,['itinerary_id'])) \
									.merge(otp_suggestions, 
											left_on=['o_boarding_id','itinerary_id'],
											right_on=['user_trip_id','itinerary_id'], 
											how='inner') \
									.query('mode == \'BUS\'') \
									.assign(first_vehicle_boarding = lambda x: np.where(np.logical_not(x['o_busCode'].str.isdigit()) & (
																						x['o_route'] == x['route']),
																						  True,
																						  False)) \
									.filter(np.append(otp_suggestions.columns.values,['first_vehicle_boarding','o_busCode','o_tripNum','o_boarding_datetime']))
	return otp_legs_suggestions_matches

def match_otp_legs_start_to_buste(otp_filtered_legs,bus_trips):
	otp_legs_buste_start = otp_filtered_legs \
							.merge(bus_trips, 
									 left_on=['route','from_stop_id'], 
									 right_on=['route','stopPointId'], 
									 how='inner') \
							.assign(otp_buste_start_timediff = 
								lambda x: np.absolute(x['gps_datetime'] - x['otp_start_time'])) \
							.filter(['user_trip_id','first_vehicle_boarding','itinerary_id','leg_id','route','busCode',
								 'o_busCode','tripNum','o_tripNum','from_stop_id','otp_start_time','gps_datetime',
								 'o_boarding_datetime','otp_buste_start_timediff','to_stop_id','otp_end_time']) \
							.sort_values(['user_trip_id','itinerary_id','leg_id','otp_buste_start_timediff']) \
							.rename(index=str, columns={'to_stop_id':'stopPointId', 'gps_datetime':'matched_start_time'})
				
	otp_legs_buste_start = otp_legs_buste_start[otp_legs_buste_start['otp_buste_start_timediff'] < pd.Timedelta('60min')]
	return otp_legs_buste_start

def match_otp_legs_end_to_buste(otp_filtered_legs,bus_trips):
	otp_legs_buste = otp_legs_buste_start \
				.merge(bus_trips, 
						 on=['route','busCode','tripNum','stopPointId'], 
						 how='inner') \
				.assign(otp_buste_end_timediff = 
							lambda x: np.absolute(x['gps_datetime'] - x['otp_end_time'])) \
				.rename(index=str, columns={'stopPointId':'to_stop_id', 'gps_datetime':'matched_end_time'}) \
				.assign(leg_duration = lambda x: x['matched_end_time'] - x['matched_start_time'],
						boarding_otp_match_start_timediff = 
							lambda x: np.absolute(x['o_boarding_datetime'] - x['matched_start_time'])) \
				.query('matched_end_time > matched_start_time') \
				.filter(['user_trip_id','first_vehicle_boarding','itinerary_id','leg_id','route','busCode',
						 'o_busCode','tripNum','o_tripNum','from_stop_id','otp_start_time',
						 'matched_start_time','o_boarding_datetime','otp_buste_start_timediff',
						 'to_stop_id','otp_end_time','matched_end_time','otp_buste_end_timediff',
						 'boarding_otp_match_start_timediff', 'leg_duration']) \
				.sort_values(['user_trip_id','itinerary_id','leg_id','otp_buste_end_timediff'])

	otp_legs_buste = otp_legs_buste[otp_legs_buste['otp_buste_end_timediff'] < pd.Timedelta('60min')]
	return otp_legs_buste

def add_stops_data_to_leg_matches(chosen_leg_matches,stops_locations):
	chosen_leg_matches_data = chosen_leg_matches.merge(stops_locations, left_on='from_stop_id', right_on='stop_id', how='left') \
										.drop('stop_id', axis=1) \
										.rename(index=str, columns={'stop_lat':'from_stop_lat','stop_lon':'from_stop_lon'}) \
										.merge(stops_locations, left_on='to_stop_id', right_on='stop_id', how='left') \
										.drop('stop_id', axis=1) \
										.rename(index=str, columns={'stop_lat':'to_stop_lat','stop_lon':'to_stop_lon'}) \
										.merge(user_trips_ids, on=['user_trip_id'], how='inner') \
										[np.append(np.append(['cardNum'],otp_legs_buste.columns.values),['from_stop_lat','from_stop_lon','to_stop_lat','to_stop_lon'])]
	return chosen_leg_matches_data

def build_candidate_itineraries_df(chosen_leg_matches_data):
	otp_buste_itineraries = chosen_leg_matches_data \
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
	return otp_buste_itineraries

def get_candidate_itineraries_summary(candidate_itineraries,boarding_suggestions_matches):
	otp_buste_itineraries_summary = candidate_itineraries \
					.merge(boarding_suggestions_matches \
								.drop_duplicates(subset=['cardNum','user_trip_id','itinerary_id']),
							on=['cardNum','user_trip_id','itinerary_id'], 
							how='inner') \
					[['cardNum', 'user_trip_id', 'itinerary_id',
						  'match_from_stop_id', 'match_matched_start_time', 'o_boarding_datetime',
						  'match_from_stop_lat', 'match_from_stop_lon', 'o_stop_lat', 'o_stop_lon',
						  'match_to_stop_id', 'match_matched_end_time', 'next_o_boarding_datetime',
						  'match_to_stop_lat', 'match_to_stop_lon', 'next_o_stop_lat', 'next_o_stop_lon','match_num_transfers', 'match_vehicle_boarding']] \
					.assign(start_diff = lambda x: np.absolute(x['match_matched_start_time'] - x['o_boarding_datetime']),
							trip_duration = lambda x: x['match_matched_end_time'] - x['match_matched_start_time'],
							origin_dist = lambda y: y.apply(lambda x: dist(x['match_from_stop_lat'], x['match_from_stop_lon'], x['o_stop_lat'], x['o_stop_lon']),axis=1),
							next_origin_dist = lambda y: y.apply(lambda x: dist(x['match_to_stop_lat'], x['match_to_stop_lon'], x['next_o_stop_lat'], x['next_o_stop_lon']),axis=1)) \
					.sort_values(['cardNum','user_trip_id'])

	otp_buste_itineraries_summary = otp_buste_itineraries_summary[((otp_buste_itineraries_summary['trip_duration'] > pd.Timedelta('0s')) & 
																	(otp_buste_itineraries_summary['trip_duration'] < pd.Timedelta('2h'))) &
													   			((otp_buste_itineraries_summary['start_diff'] > pd.Timedelta('0s')) & 
																	(otp_buste_itineraries_summary['start_diff'] < pd.Timedelta('1.5h')))] \
										.query('origin_dist < 0.1') \
										.query('next_origin_dist < 2.0')
	return otp_buste_itineraries_summary

def get_candidate_itineraries_penalty_score(otp_buste_itineraries_filtered):
	otp_buste_itineraries_penalty = otp_buste_itineraries_filtered \
							.assign(penalty = lambda x: 2*x['start_diff'].dt.total_seconds() + x['trip_duration'].dt.total_seconds() + x['match_num_transfers']*10) \
							[['cardNum','user_trip_id','itinerary_id','match_num_transfers','match_vehicle_boarding','next_origin_dist','origin_dist','start_diff','trip_duration','penalty']] \
							.sort_values(['user_trip_id','penalty'], ascending=True)
	return otp_buste_itineraries_penalty


#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print "Error: Wrong Usage!"
        printUsage()
        sys.exit(1)

otp_suggestions_filepath = sys.argv[1]
enhanced_buste_folderpath = sys.argv[2]
gtfs_base_folderpath = sys.argv[3]
output_folderpath = sys.argv[4]

file_date_str = otp_suggestions_filepath.split('/')[-1].split('_user_trips_')[0]
file_date = pd.to_datetime(file_date_str,format='%Y_%m_%d')
print "Processing File:", otp_suggestions_filepath

# Read OTP Suggestions
otp_suggestions_raw = pd.read_csv(otp_suggestions_filepath, parse_dates=['date','otp_start_time','otp_end_time'])

# Prepare OTP data for analysis
otp_suggestions = prepare_otp_data(otp_suggestions_raw)

# Read stops data
stops_filepath = gtfs_base_folderpath + os.sep + get_router_id(file_date) + os.sep + 'stops.txt'
stops_df = pd.read_csv(stops_filepath)

# Adding Parent Stop data to OTP Suggestions
stops_parent_stations = stops_df[['stop_id','parent_station']]
otp_suggestions = otp_suggestions.merge(stops_parent_stations, 
										left_on='from_stop_id', 
										right_on='stop_id', 
										how='left') \
							.drop(['stop_id'], axis=1)

# Read Origin/Next-Origin Pairs for the same date
trips_origins_filepath = enhanced_buste_folderpath + os.sep + file_date_str + '_user_trips.csv'
trips_origins = pd.read_csv(trips_origins_filepath, 
					parse_dates=['o_boarding_datetime','o_gps_datetime','next_o_boarding_datetime','next_o_gps_datetime'])

# Checking whether OTP and ticketing dates match
dates_compatibility, otp_date, ticketing_date = compatible_dates(otp_suggestions,trips_origins)
if not dates_compatibility:
	print "ERROR: OTP date", otp_date, "does not match Ticketing data", ticketing_date
	print "Skipping current day"
	exit(1)

# Selecting trips for whom OTP suggestions were found
selected_trips = trips_origins[trips_origins['o_boarding_id'].isin(otp_suggestions['user_trip_id'])]
num_selected_trips = len(selected_trips)

# Matching all kinds of boarding events to valid OTP suggestions
itineraries_start = otp_suggestions.query('mode == \'BUS\'') \
			.groupby(['user_trip_id','itinerary_id']) \
			.first() \
			.reset_index()

# Matching vehicle boarding origins
matched_vehicle_boardings,num_matched_vehicle_boardings,vehicle_match_perc = match_vehicle_boardings(selected_trips,itineraries_start)
print "Vehicle boardings with matching OTP suggestions: ", num_matched_vehicle_boardings, "(",vehicle_match_perc, "%)"


# Matching terminal boarding origins
matched_terminal_boardings,num_matched_terminal_boardings,terminal_matched_perc = match_terminal_boardings(selected_trips,itineraries_start)
print "Terminal boardings with matching OTP suggestions: ", num_matched_terminal_boardings, "(", terminal_matched_perc, "%)"

# Matching special case route 021 terminal boarding origins 
num_terminal_021_boardings,matched_021_terminal_boardings,num_matched_021_terminal_boardings,terminal_021_match_perc = match_terminal_021_boardings(selected_trips,itineraries_start)
if (num_terminal_021_boardings > 0):
	print "Line 021 Terminal boardings with matching OTP suggestions: ", num_matched_021_terminal_boardings, "(",terminal_021_match_perc, "%)"
else:
	print "No Line 021 Terminal boardings found. Skipping matching."

boarding_suggestions_matches = pd.concat([matched_vehicle_boardings,matched_021_terminal_boardings,matched_terminal_boardings]) 
total_num_matches = num_matched_vehicle_boardings + num_matched_021_terminal_boardings + num_matched_terminal_boardings
print "Total number of matches: ", total_num_matches, "(", 100*(total_num_matches/float(num_selected_trips)), "%)"

# Add OTP extra origin/next-origin pairs to final dataset
otp_filtered_legs = get_otp_matched_legs(boarding_suggestions_matches,otp_suggestions)

# Find OTP Suggested Itineraries in BUSTE Data
bus_trips_filepath = enhanced_buste_folderpath + os.sep + file_date_str + '_bus_trips.csv'
bus_trips = pd.read_csv(bus_trips_filepath, dtype={'route': object},parse_dates=['gps_datetime']) \
				.sort_values(['route','busCode','tripNum','gps_datetime']) \
				.assign(route = lambda x: x['route'].astype(str).str.replace("\.0",'').str.zfill(3))

# Find legs candidate match start point
otp_legs_buste_start = match_otp_legs_start_to_buste(otp_filtered_legs,bus_trips)

# Find legs end point
otp_legs_buste = match_otp_legs_end_to_buste(otp_legs_buste_start,bus_trips)

# Choosing best leg match using current and previous leg information
legs_matches_groups = otp_legs_buste.groupby(['user_trip_id','itinerary_id','leg_id'])
chosen_leg_matches = choose_leg_matches(legs_matches_groups)

# Choosing itinerary
# Adding stops location data
stops_locations = stops_df[['stop_id','stop_lat','stop_lon']]
user_trips_ids = boarding_suggestions_matches[['cardNum','user_trip_id']] \
					.drop_duplicates() \
					.sort_values(['cardNum','user_trip_id'])

chosen_leg_matches_data = add_stops_data_to_leg_matches(chosen_leg_matches,stops_locations)

# Summarizing suggested itineraries information
candidate_itineraries = build_candidate_itineraries_df(chosen_leg_matches_data)
candidate_itineraries_filtered = get_candidate_itineraries_summary(candidate_itineraries,boarding_suggestions_matches)

# Assigning suggested itineraries a penalty score
otp_buste_itineraries_penalty = get_candidate_itineraries_penalty_score(candidate_itineraries_filtered)

# Choose best itineraries based on the penalty score
chosen_itineraries = otp_buste_itineraries_penalty.groupby(['user_trip_id']).first().reset_index()

# Filtering chosen itineraries
chosen_itineraries = chosen_itineraries[(np.logical_not(chosen_itineraries['match_vehicle_boarding'])) | 
										((chosen_itineraries['match_vehicle_boarding']) 
										& (chosen_itineraries['start_diff'] < pd.Timedelta('20 min')))]
num_chosen_itineraries = len(chosen_itineraries)

print "Final number of matches (after processing): ", len(chosen_itineraries) , "(", 100*(num_chosen_itineraries/float(num_selected_trips)), "%)"

# Building final Origin-Destination Trips dataframe
od_trips = chosen_itineraries.merge(chosen_leg_matches_data, on=['cardNum','user_trip_id','itinerary_id'], how='inner') \
								.filter(['cardNum','user_trip_id','itinerary_id','leg_id','route','busCode','tripNum',
										'from_stop_id','matched_start_time','from_stop_lat','from_stop_lon','to_stop_id',
										'matched_end_time','to_stop_lat','to_stop_lon','leg_duration']) \
								.rename(index=str, columns={'matched_start_time':'start_time','matched_end_time':'end_time'})

# Writing final OD Trips dataset to file
itinerary_part_name = otp_suggestions_filepath.split('/')[-1].split('_')[5]
output_filepath = output_folderpath + os.sep + file_date_str + '_' + itinerary_part_name + '_od_trips.csv'
od_trips.to_csv(output_filepath,index=False)

