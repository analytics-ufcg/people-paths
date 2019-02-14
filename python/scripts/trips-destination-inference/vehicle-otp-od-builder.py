#Libraries

#Python Libs
import sys
import os
import glob
import traceback
from datetime import datetime
import time
from geopy import distance


#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 6

#Functions
def printUsage():
    print "Usage: " + sys.argv[0] + " <otp-suggestions-filepath> <user-trips-folderpath> <bus-trips-folderpath> <gtfs-base-folderpath> <output-folderpath>"

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

def get_router_id(query_date):
    INTERMEDIATE_OTP_DATE = pd.to_datetime("2017-06-30", format="%Y-%m-%d")
    router_id = ''

    if (query_date <= INTERMEDIATE_OTP_DATE):
        return 'ctba-2017-1'
    else:
        return 'ctba-2017-2'

def prepare_otp_data(otp_data):
        #Fixing prefix
        otp_data.columns = otp_data.columns.str.replace('otp_','')
        otp_data = otp_data.add_prefix('otp_')
        
        #Fixing Timezone difference - when needed
        otp_data['otp_start_time'] = otp_data['otp_start_time'] - pd.Timedelta('10800 s')
        otp_data['otp_end_time'] = otp_data['otp_end_time'] - pd.Timedelta('10800 s')
        
        #Adjusting route format to have 3 numbers
        otp_data['otp_route'] = otp_data['otp_route'].astype(str)
        otp_data['otp_route'] = np.where(otp_data['otp_mode'] == 'BUS',
                            otp_data['otp_route'].astype(str).str.replace("\.0",'').str.zfill(3),
                            otp_data['otp_route'])

        return otp_data

def compatible_dates(otp_data,ticketing_data):
        otp_date = otp_data['otp_date'].iloc[0]
        ticketing_date = pd.to_datetime(ticketing_data['o_boarding_datetime'].dt.strftime('%Y-%m-%d')[0])

        return (otp_date == ticketing_date,otp_date,ticketing_date)

def match_vehicle_boardings(selected_trips,itineraries_st):
        vehicle_boarding_origins = selected_trips[np.logical_not(selected_trips['o_busCode'].str.isdigit())]
        matched_vehicle_boardings = vehicle_boarding_origins.merge(itineraries_st, left_on=['o_boarding_id','o_route','o_stopPointId'], 
                                                                   right_on=['otp_user_trip_id','otp_route','otp_from_stop_id'], how='inner')
        num_matched_vehicle_boardings = len(matched_vehicle_boardings.drop_duplicates(subset=['o_boarding_id']))
        if num_matched_vehicle_boardings == 0:
            match_perc = 0.0
        else:
            match_perc = 100*(num_matched_vehicle_boardings/float(len(vehicle_boarding_origins)))
        return (matched_vehicle_boardings,num_matched_vehicle_boardings,len(vehicle_boarding_origins),match_perc)

def is_new_itinerary(prev_trip_id,curr_trip_id,prev_itin_id,curr_itin_id):
    return ((prev_trip_id != curr_trip_id) | (prev_itin_id != curr_itin_id))    

def choose_leg_matches(leg_matches_groups):
        colnames = leg_matches_groups.obj.columns.values
        chosen_leg_matches = pd.DataFrame(columns = colnames)
        prev_trip_id = -1
        prev_itin_id = -1
        prev_leg_mode = ""
        prev_leg_end_time = pd.NaT
        num_groups_not_survived = 0
        new_itinerary = False

        for name, group in leg_matches_groups:
            
                #print
                #print "Name:", name
                #print "Group:"
                #print group
                #print
                
                curr_trip_id = group['otp_user_trip_id'].iloc[0]
                curr_itin_id = group['otp_itinerary_id'].iloc[0]
                curr_leg_id = group['otp_leg_id'].iloc[0]
                curr_leg_mode = group['otp_mode'].iloc[0]
                
                new_itinerary = is_new_itinerary(prev_trip_id,curr_trip_id,prev_itin_id,curr_itin_id)
                if new_itinerary:
                    prev_leg_end_time = group['otp_start_time'].dt.floor('d').iloc[0]

                #if (prev_group_id == ()):
                #        prev_leg_end_time = group['bt_start_time'].dt.floor('d')[0]

                #print
                #print "Previous itinerary id:", prev_itin_id
                #print "Previous leg mode:", prev_leg_mode
                #print "Previous leg end time:", prev_leg_end_time
                #print "Current leg id:", curr_leg_id
                #print "Current leg mode:", curr_leg_mode
                #print
                #print "Original Group"
                #print group.filter(['otp_start_time','bt_start_time','bt_end_time'])
                
                if (curr_leg_mode == 'WALK'):
                    #print "Walking duration:", filtered_group['otp_duration_mins']
                    filtered_group = group.reset_index()
                    if new_itinerary: #first leg is a WALK leg
                        filtered_group.loc[0,'bt_end_time'] = prev_leg_end_time
                    else:
                        filtered_group.loc[0,'bt_start_time'] = prev_leg_end_time
                        filtered_group.loc[0,'bt_end_time'] = prev_leg_end_time + \
                            pd.Timedelta(minutes=np.rint(filtered_group['otp_duration_mins'].iloc[0]))
                    #print "Filtered Group"
                    #print filtered_group
                else:
                    filtered_group = group[group['bt_start_time'] > prev_leg_end_time]
                
                #print
                #print "Filtered Group"
                #print filtered_group.filter(['otp_start_time','bt_start_time','bt_end_time'])

                if (len(filtered_group) == 0):
                        #print "Group did not survive! =("
                        #print
                        #print "Previous itinerary id:", prev_itin_id
                        #print "Previous leg mode:", prev_leg_mode
                        #print "Previous leg end time:", prev_leg_end_time
                        #print "Current leg id:", curr_leg_id
                        #print "Current leg mode:", curr_leg_mode
                        #print
                        #print "Original Group"
                        #print group#.filter(['otp_start_time','bt_start_time','bt_end_time'])
                        num_groups_not_survived += 1
                        continue

                chosen_leg_match = filtered_group.sort_values('bt_start_time').iloc[0]
                
                if ((curr_leg_id == 2) & 
                    ((curr_leg_mode == 'BUS') & (prev_leg_mode == 'WALK'))):
                        #Update previous walk start/end_times
                        #print
                        #print "Chosen Leg Matches"
                        #print chosen_leg_matches.iloc[-1]
                        #print
                        chosen_leg_matches.iloc[-1,chosen_leg_matches.columns.get_loc('bt_start_time')] = chosen_leg_match['bt_start_time'] - \
                            pd.Timedelta(minutes=np.rint(chosen_leg_matches.iloc[-1].otp_duration_mins))
                        chosen_leg_matches.iloc[-1,chosen_leg_matches.columns.get_loc('bt_end_time')] = chosen_leg_match['bt_start_time']
                #print "Chosen Leg"
                #print chosen_leg_match

                chosen_leg_matches = chosen_leg_matches.append(chosen_leg_match)

                #Update variables
                #prev_group_id = name
                prev_trip_id = curr_trip_id
                prev_itin_id = curr_itin_id
                prev_leg_mode = curr_leg_mode
                prev_leg_end_time = chosen_leg_match['bt_end_time']

        #print "Number of groups which did not survive:", num_groups_not_survived
        return chosen_leg_matches.filter(colnames)


def add_stops_data_to_legs(itineraries_legs,stops_locs):
    itineraries_legs_stops = itineraries_legs.merge(stops_locs, left_on='otp_from_stop_id', right_on='stop_id', how='left') \
                                                                                .drop('stop_id', axis=1) \
                                                                                .rename(index=str, columns={'stop_lat':'from_stop_lat','stop_lon':'from_stop_lon'}) \
                                                                                .merge(stops_locations, left_on='otp_to_stop_id', right_on='stop_id', how='left') \
                                                                                .drop('stop_id', axis=1) \
                                                                                .rename(index=str, columns={'stop_lat':'to_stop_lat','stop_lon':'to_stop_lon'}) 
    return itineraries_legs_stops

def build_candidate_itineraries_df(chosen_leg_matches_data):
        itins_bus_info = chosen_leg_matches_data \
                                        .query('otp_mode == \'BUS\'') \
                                        .groupby(['card_num','trip_id','otp_itinerary_id']) \
                                        .agg({'otp_from_stop_id': lambda x: x.iloc[0],
                                              'from_stop_lat': lambda x: x.iloc[0],
                                              'from_stop_lon': lambda x: x.iloc[0],
                                              'otp_to_stop_id': lambda x: x.iloc[-1],
                                              'to_stop_lat': lambda x: x.iloc[-1],
                                              'to_stop_lon': lambda x: x.iloc[-1],
                                              'otp_mode': lambda x: len(x)}) \
                                        .reset_index() \
                                        .rename(index=str, columns={'otp_mode':'num_transfers',
                                                                    'otp_from_stop_id':'from_stop_id',
                                                                    'otp_to_stop_id':'to_stop_id'})
        itins_time_info = chosen_leg_matches_data \
                                        .groupby(['card_num','trip_id','otp_itinerary_id']) \
                                        .agg({'bt_start_time': lambda x: x.iloc[0],
                                              'bt_end_time': lambda x: x.iloc[-1],
                                              'otp_start_time': lambda x: x.iloc[0],
                                              'otp_end_time': lambda x: x.iloc[-1],
                                              'date': lambda x: x.iloc[0]}) \
                                        .reset_index() \
                                        .rename(index=str, columns={'otp_start_time':'sch_start_time',
                                                                    'otp_end_time':'sch_end_time',
                                                                    'bt_start_time':'obs_start_time',
                                                                    'bt_end_time':'obs_end_time'}) 
        
        otp_buste_itineraries = itins_bus_info.merge(itins_time_info) \
                                        .reindex(['date','card_num','trip_id','otp_itinerary_id',
                                                  'from_stop_id','sch_start_time','obs_start_time',
                                                  'from_stop_lat','from_stop_lon','to_stop_id',
                                                  'sch_end_time','obs_end_time','to_stop_lat',
                                                  'to_stop_lon','num_transfers'], axis=1, copy=False)\
                                        .assign(card_num = lambda x: x['card_num'].astype(float),
                                                trip_id = lambda x: x['trip_id'].astype(float),
                                                otp_itinerary_id = lambda x: x['otp_itinerary_id'].astype(float))
        return otp_buste_itineraries


def dist(p1_lat, p1_lon, p2_lat, p2_lon):
    if(np.isnan([p1_lat, p1_lon, p2_lat, p2_lon]).any()):
        return -1
    else:
        return np.around(distance.geodesic((p1_lat,p1_lon),(p2_lat,p2_lon)).km,decimals=5)

def get_candidate_itineraries_summary(candidate_itineraries,trips_validation):
        otp_buste_itineraries_summary = candidate_itineraries \
                                        .merge(trips_validation,how='inner') \
                                        .assign(start_diff = lambda x: np.absolute(x['obs_start_time'] - x['o_boarding_datetime']),
                                                origin_dist = lambda y: y.apply(lambda x: dist(x['from_stop_lat'], x['from_stop_lon'], x['o_stop_lat'], x['o_stop_lon']),axis=1),
                                                next_origin_dist = lambda y: y.apply(lambda x: dist(x['to_stop_lat'], x['to_stop_lon'], x['next_o_stop_lat'], x['next_o_stop_lon']),axis=1),
                                                next_start_diff = lambda x: np.absolute(x['next_o_boarding_datetime'] - x['obs_end_time']),
                                                sch_duration_mins = lambda x: 
                                                (x.sch_end_time - x.sch_start_time)/pd.Timedelta('1m'),
                                                obs_duration_mins = lambda x:
                                                (x.obs_end_time - x.obs_start_time)/pd.Timedelta('1m')) \
                                        .sort_values(['card_num','trip_id'])
        return otp_buste_itineraries_summary




#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print "Error: Wrong Usage!"
        printUsage()
        sys.exit(1)

otp_suggestions_filepath = sys.argv[1]
user_trips_folderpath = sys.argv[2]
bus_trips_folderpath = sys.argv[3]
gtfs_base_folderpath = sys.argv[4]
output_folderpath = sys.argv[5]

file_date_str = otp_suggestions_filepath.split('/')[-1].split('_user_trips_')[0]
file_date = pd.to_datetime(file_date_str,format='%Y_%m_%d')
print "Processing File:", otp_suggestions_filepath

try:

	exec_start_time = time.time()

	# Extracting itinerary part name for later use
	itinerary_part_name = otp_suggestions_filepath.split('/')[-1].split('_')[5]
	# Read OTP Suggestions
	otp_suggestions_raw = pd.read_csv(otp_suggestions_filepath, parse_dates=['date','otp_start_time','otp_end_time'])

        if len(otp_suggestions_raw) == 0:
            print "Zero OTP suggestions found."
            print "Skipping next steps..."
            exit(0)

	        # Prepare OTP data for analysis
        otp_suggestions = prepare_otp_data(otp_suggestions_raw)

        # Read stops data
        stops_filepath = gtfs_base_folderpath + os.sep + get_router_id(file_date) + os.sep + 'stops.txt'
        stops_df = pd.read_csv(stops_filepath)

        # Adding Parent Stop data to OTP Suggestions
        stops_parent_stations = stops_df[['stop_id','parent_station']]
        otp_suggestions = otp_suggestions.merge(stops_parent_stations.add_prefix('from_'),
                                                left_on='otp_from_stop_id',
                                                right_on='from_stop_id',
                                                how='left') \
                                        .merge(stops_parent_stations.add_prefix('to_'),
                                                left_on='otp_to_stop_id',
                                                right_on='to_stop_id',
                                                how='left') \
                                        .drop(['from_stop_id','to_stop_id'], axis=1) \
                                        .rename(index=str, columns={'from_parent_station':'otp_from_parent_station',
                                                                    'to_parent_station':'otp_to_parent_station'})
        
        otp_suggestions_bus_legs = otp_suggestions[otp_suggestions['otp_mode'] == 'BUS']
        otp_suggestions_walk_legs = otp_suggestions[otp_suggestions['otp_mode'] == 'WALK']

	# Read and Prepare Origin/Next-Origin Pairs data
        trips_origins_filepath = user_trips_folderpath + os.sep + file_date_str + '_user_trips.csv'
        trips_on_pairs_full = pd.read_csv(trips_origins_filepath,
                                                parse_dates=['o_boarding_datetime','o_gps_datetime','next_o_boarding_datetime','next_o_gps_datetime'])
        # Checking whether OTP and ticketing dates match
        dates_compatibility, otp_date, ticketing_date = compatible_dates(otp_suggestions,trips_on_pairs_full)
        if not dates_compatibility:
                print "ERROR: OTP date", otp_date, "does not match Ticketing data", ticketing_date
                print "Skipping current day"
                exit(1)
        
        trips_on_pairs = trips_on_pairs_full.filter(['o_boarding_id','next_o_boarding_id'])
        trips_origins = trips_on_pairs_full.filter([col for col in trips_on_pairs_full.columns if col.startswith('o_')])	

	# Filtering out non-vehicle-boarding itinerary suggestions
	vehicle_boarding_trip_ids = trips_origins[np.logical_not(trips_origins['o_busCode'].str.isdigit())].o_boarding_id

	otp_suggestions_vehicle = otp_suggestions[otp_suggestions['otp_user_trip_id'].isin(vehicle_boarding_trip_ids)]
	otp_suggestions_bus_legs = otp_suggestions_vehicle[otp_suggestions_vehicle['otp_mode'] == 'BUS']
	otp_suggestions_walk_legs = otp_suggestions_vehicle[otp_suggestions_vehicle['otp_mode'] == 'WALK']

	# Read and Prepare Bus Trips Data
        bus_trips_filepath = bus_trips_folderpath + os.sep + file_date_str + '_bus_trips.csv'
        bus_trips = pd.read_csv(bus_trips_filepath, dtype={'route': object},parse_dates=['gps_datetime']) \
                                        .sort_values(['route','busCode','tripNum','gps_datetime']) \
                                        .assign(route = lambda x: x['route'].astype(str).str.replace("\.0",'').str.zfill(3))  \
                                        .drop_duplicates()

	bus_trips_clean = bus_trips.filter(['route','busCode','tripNum','stopPointId','gps_datetime'])

	# Identify Possible Matches between OTP Itineraries and Bus Trips Observed Data
	scheduled_itin_observed_o = otp_suggestions_bus_legs.merge(bus_trips_clean.add_prefix('bt_'),
                                left_on=['otp_route','otp_from_stop_id'],
                                right_on=['bt_route','bt_stopPointId'],
                                how='inner') \
                                .drop(['bt_route','bt_stopPointId'], axis=1) \
                                .rename(index=str, columns={'bt_gps_datetime':'bt_start_time',
                                                            'bt_tripNum':'bt_trip_num',
                                                            'bt_busCode':'bt_bus_code'}) \
                                .assign(sched_obs_start_timediff = 
                                        lambda x: np.absolute(x['bt_start_time'] - x['otp_start_time']))

	scheduled_itin_observed_od = scheduled_itin_observed_o.merge(bus_trips_clean.add_prefix('bt_'),
                                left_on=['otp_route','bt_bus_code','bt_trip_num','otp_to_stop_id'],
                                right_on=['bt_route','bt_busCode','bt_tripNum','bt_stopPointId'],
                                how='inner') \
                                .drop(['bt_route','bt_stopPointId'], axis=1) \
                                .rename(index=str, columns={'bt_gps_datetime':'bt_end_time'}) \
                                .assign(sched_obs_end_timediff = 
                                        lambda x: np.absolute(x['bt_end_time'] - x['otp_end_time'])) \
                                .sort_values(['otp_user_trip_id','otp_itinerary_id','otp_leg_id','sched_obs_start_timediff','sched_obs_end_timediff'])

	scheduled_itin_observed_od['bt_duration_mins'] = (scheduled_itin_observed_od['bt_end_time'] - scheduled_itin_observed_od['bt_start_time'])/pd.Timedelta(minutes=1)
	scheduled_itin_observed_od = scheduled_itin_observed_od[scheduled_itin_observed_od['bt_duration_mins'] > 0]

	scheduled_itin_observed_od_full = pd.concat([scheduled_itin_observed_od,otp_suggestions_walk_legs], sort=False)

	scheduled_itin_observed_od_full_clean = scheduled_itin_observed_od_full \
                            .filter(['otp_user_trip_id','otp_itinerary_id','otp_leg_id','otp_mode','otp_route',
                                     'bt_bus_code','bt_trip_num','otp_from_stop_id','otp_start_time',
                                     'bt_start_time','sched_obs_start_timediff','otp_to_stop_id',
                                     'otp_end_time','bt_end_time','sched_obs_end_timediff','otp_duration_mins']) \
                            .sort_values(['otp_user_trip_id','otp_itinerary_id','otp_leg_id'])

	# Working with Vehicle Boardings
        # Selecting trips for whom OTP suggestions were found
        selected_trips = trips_origins[trips_origins['o_boarding_id'].isin(otp_suggestions_vehicle['otp_user_trip_id'])]
        num_selected_trips = len(selected_trips)

	# Matching all kinds of boarding events to valid OTP suggestions
        itins_first_bus_legs = otp_suggestions_bus_legs \
                                .groupby(['otp_user_trip_id','otp_itinerary_id']) \
                                .first() \
                                .reset_index()

        # Matching vehicle boarding origins
        matched_vehicle_boardings,num_matched_vehicle_boardings,num_vehicle_boardings,vehicle_match_perc = match_vehicle_boardings(selected_trips,itins_first_bus_legs)
        print "Vehicle boardings with matching OTP suggestions: ", num_matched_vehicle_boardings, "(",vehicle_match_perc, "%)"

        total_num_matches = num_matched_vehicle_boardings
        print "Initial number of itinerary matches: ", total_num_matches, "(", 100*(total_num_matches/float(num_vehicle_boardings)), "%)"

        if total_num_matches == 0:
            print "No match was found. Skipping next steps..."
            exit(0)

	vehic_first_boardings_options = matched_vehicle_boardings.merge(bus_trips_clean, 
                                left_on=['o_route','o_busCode','o_tripNum','otp_to_stop_id'],
                               right_on=['route','busCode','tripNum','stopPointId'],
                               how='inner') \
            
	# Retain only OTP-BusTrips itineraries which figure in first-vehicle-boarding matched itineraries
	matched_vehicle_boardings_itins = vehic_first_boardings_options.filter(['otp_user_trip_id','otp_itinerary_id'])
	vehicle_boardings_obs_sch_itin_legs = scheduled_itin_observed_od_full_clean.merge(matched_vehicle_boardings_itins,how='inner') \
                                        .sort_values(['otp_user_trip_id','otp_itinerary_id','otp_leg_id'])
	
	# Concatenating first boarding legs to other itinerary legs
	# Preparing First Boarding legs data
	vehic_first_boardings_options_clean = vehic_first_boardings_options \
		.filter(['otp_user_trip_id','otp_itinerary_id','otp_leg_id','otp_mode','otp_route','o_busCode',
			'o_tripNum','otp_from_stop_id','otp_start_time','o_boarding_datetime','otp_to_stop_id',
			'otp_end_time','gps_datetime','otp_duration_mins']) \
		.rename(index=str, columns={'o_busCode':'bt_bus_code','o_tripNum':'bt_trip_num',
						'o_boarding_datetime':'bt_start_time','gps_datetime':'bt_end_time'}) \
		.assign(bt_duration_mins = lambda x: (x.bt_end_time - x.bt_start_time)/pd.Timedelta(minutes=1))

	# Preparing OTP itinerary legs data
	vehicle_boardings_obs_sch_itin_legs_clean = vehicle_boardings_obs_sch_itin_legs \
		.filter(['otp_user_trip_id','otp_itinerary_id','otp_leg_id','otp_mode','otp_route','bt_bus_code',
			'bt_trip_num','otp_from_stop_id','otp_start_time','bt_start_time','otp_to_stop_id',
			'otp_end_time','bt_end_time','otp_duration_mins'])\
		.assign(bt_duration_mins = lambda x: (x.bt_end_time - x.bt_start_time)/pd.Timedelta(minutes=1))

	# Concatenating Legs
	vehic_first_boardings_options_clean_keys = vehic_first_boardings_options_clean.filter(['otp_user_trip_id','otp_itinerary_id','otp_leg_id']).drop_duplicates()
	vehicle_legs_merged = vehicle_boardings_obs_sch_itin_legs_clean.merge(vehic_first_boardings_options_clean_keys, how='outer', indicator=True)
	vehicle_legs_rest_clean = vehicle_legs_merged[vehicle_legs_merged['_merge'] == 'left_only'].drop('_merge', axis=1)
	all_vehicle_legs_options = pd.concat([vehic_first_boardings_options_clean,vehicle_legs_rest_clean]) \
		.sort_values(['otp_user_trip_id','otp_itinerary_id','otp_leg_id','bt_start_time'])

	# Filtering out itineraries which lost bus legs along the processing
	original_suggested_itins_num_legs = otp_suggestions.groupby(['otp_user_trip_id','otp_itinerary_id']) \
                                    .agg({'otp_leg_id': lambda x: len(x)}) \
                                    .reset_index() \
                                    .rename(index=str, columns={'otp_leg_id':'num_legs'})

	curr_matched_itins_num_legs = all_vehicle_legs_options.groupby(['otp_user_trip_id','otp_itinerary_id']) \
                                    .agg({'otp_leg_id': lambda x: len(np.unique(x))}) \
                                    .reset_index() \
                                    .rename(index=str, columns={'otp_leg_id':'num_legs'})

	complete_matched_itins = original_suggested_itins_num_legs.merge(curr_matched_itins_num_legs, how='inner')
	
	all_complete_vehicle_legs_options = all_vehicle_legs_options.merge(complete_matched_itins.drop('num_legs', axis=1), how='inner')

	# Choose best actual leg matches (based on feasibility and start time)
	feasible_legs = choose_leg_matches(all_vehicle_legs_options.groupby(['otp_user_trip_id','otp_itinerary_id','otp_leg_id']))
	
	if len(feasible_legs) == 0:
            print "No matches left after matching and selecting feasible bus legs."
            print "Skipping next steps..."
            exit(0)

	# Filtering out itineraries which lost bus legs after feasible legs choice processing
	feasible_itins_num_legs = feasible_legs.groupby(['otp_user_trip_id','otp_itinerary_id']) \
                                    .agg({'otp_leg_id': lambda x: len(x)}) \
                                    .reset_index() \
                                    .rename(index=str, columns={'otp_leg_id':'num_legs'})

	feasible_complete_itins = feasible_itins_num_legs.merge(original_suggested_itins_num_legs,how='inner')

	feasible_complete_itins_legs = feasible_legs.merge(feasible_complete_itins.drop('num_legs', axis=1),how='inner')

	# Perform an endogenous validation using location and time features
	# Add stops data to legs
	stops_locations = stops_df[['stop_id','stop_lat','stop_lon']]
	itineraries_legs = add_stops_data_to_legs(feasible_complete_itins_legs,stops_locations)

	# Add card number and date
	passenger_trips_ids = trips_on_pairs_full.filter(['cardNum','o_boarding_id']) \
                            .rename(index=str, columns={'cardNum':'card_num','o_boarding_id':'trip_id'})

	pass_itins_legs = itineraries_legs.merge(passenger_trips_ids, 
                       left_on=['otp_user_trip_id'], 
                       right_on=['trip_id'],
                       how='left') \
                .drop('otp_user_trip_id', axis=1) \
                .assign(date = lambda x: x.otp_start_time.dt.floor('d')) \
                .filter(np.append(['date','card_num','trip_id'],itineraries_legs.columns.values[1:])) \
                .sort_values(['card_num','trip_id','otp_itinerary_id','otp_leg_id'])

	# Summarizing suggested itineraries information
	cand_itineraries_df = build_candidate_itineraries_df(pass_itins_legs)

	# Add origin/next-origin locations to summarized itineraries
	passenger_trips_valid_df = trips_on_pairs_full.filter(['cardNum','o_boarding_id','o_stop_lat','o_stop_lon',
								'o_boarding_datetime','next_o_stop_lat','next_o_stop_lon',
								'next_o_boarding_datetime']) \
                            .rename(index=str, columns={'cardNum':'card_num','o_boarding_id':'trip_id'})

	# Validate itineraries using boarding metadata
	cand_itineraries_loc_validation = get_candidate_itineraries_summary(cand_itineraries_df,passenger_trips_valid_df)	
	valid_candidate_itineraries = cand_itineraries_loc_validation[((cand_itineraries_loc_validation['obs_duration_mins'] > 0) & 
                                                               (cand_itineraries_loc_validation['obs_duration_mins'] < 120)) & 
                                                              ((cand_itineraries_loc_validation['start_diff'] >= pd.Timedelta('0s')) & 
                                                               (cand_itineraries_loc_validation['start_diff'] < pd.Timedelta('1.5h')))] \
                                    .query('origin_dist < 0.1') \
                                    .query('next_origin_dist < 2.0')
                                    #NEXT_START_DIFF
                                	
	#Infer user chosen itineraries from valid itineraries based on trip duration
	inferred_trip_itineraries = valid_candidate_itineraries.sort_values(['card_num','trip_id','obs_duration_mins']) \
                                .groupby(['card_num','trip_id']) \
                                .first() \
                                .reset_index()
                        
	# Writing Inferred Trips Itineraries dataset to file
	inf_trips_itineraries_output_filepath = output_folderpath + os.sep + file_date_str + '_' + itinerary_part_name + '_itins_inf_trips.csv'
	inferred_trip_itineraries.to_csv(inf_trips_itineraries_output_filepath,index=False)

	# Getting Itineraries Legs back
	inferred_trip_itineraries_legs = pass_itins_legs.merge(inferred_trip_itineraries \
                                                       .filter(['card_num','trip_id','otp_itinerary_id']),
                                                       how='inner') \
                                                .sort_values(['card_num','trip_id','otp_itinerary_id','otp_leg_id'])

	# Writing Inferred Trips Itineraries Legs dataset to file
	inf_trips_itineraries_legs_output_filepath = output_folderpath + os.sep + file_date_str + '_' + itinerary_part_name + '_legs_inf_trips.csv'
	inferred_trip_itineraries_legs.to_csv(inf_trips_itineraries_legs_output_filepath,index=False)

				
	print "Final number of itinerary matches (after processing): ", len(inferred_trip_itineraries) , "(", 100*(len(inferred_trip_itineraries)/float(num_vehicle_boardings)), "%)"

	print "Final number of itinerary leg matches: ", len(inferred_trip_itineraries_legs)



	print "Processing time:", time.time() - exec_start_time, "s"

except Exception:
	print "Error in processing file " + otp_suggestions_filepath
	traceback.print_exc(file=sys.stdout)
