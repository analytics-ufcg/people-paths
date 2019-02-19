#Libraries

#Python Libs
import sys
import os
import glob

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 5

#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <inf-itineraries-base-folder-path> <sch-obs-itineraries-base-folder-path>  <output-folder-path> <initial-date> <final-date>")

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

def get_trip_len_bucket(trip_duration):
    if (trip_duration < 10):
        return '<10'
    elif (trip_duration < 20):
        return '10-20'
    elif (trip_duration < 30):
        return '20-30'
    elif (trip_duration < 40):
        return '30-40'
    elif (trip_duration < 50):
        return '40-50'
    elif (trip_duration >= 50):
        return '50+'
    else:
        return 'NA'
    
def get_day_type(trip_start_time):
    trip_weekday = trip_start_time.weekday()
    if ((trip_weekday == 0) | (trip_weekday == 4)):
        return 'MON/FRI'
    elif ((trip_weekday > 0) & (trip_weekday < 4)):
        return 'TUE/WED/THU'
    elif (trip_weekday > 4):
        return 'SAT/SUN'
    else:
        return 'NA'

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

inf_itineraries_base_folderpath = sys.argv[1]
sch_obs_itineraries_base_folderpath = sys.argv[2]
output_folderpath = sys.argv[3]
initial_date = sys.argv[4]
final_date = sys.argv[5]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

selected_files = select_input_files(inf_itineraries_base_folderpath,initial_date_dt,final_date_dt,'_full_itins_inf_trips')

#Reading Boarding Data
for file_path,file_date in selected_files:
	file_date_str =  file_date.strftime('%Y_%m_%d')

	print "Processing date:", file_date.strftime('%Y-%m-%d')

	# Read Inferred Trips Itineraries dataset for a day
	inf_trips_itins = pd.read_csv(file_path,parse_dates=['date','sch_start_time','obs_start_time','sch_end_time','obs_end_time','o_boarding_datetime','next_o_boarding_datetime'])

	# Read schedule-observed-matched itineraries for the same day
	sch_obs_trips_itins = pd.read_csv(sch_obs_itineraries_base_folderpath + os.sep + file_date_str + '_full__sch_obs_itins.csv',
					parse_dates=['date','sch_start_time','obs_start_time','sch_end_time','obs_end_time'])

	# Prepare Datasets
	inf_trips_itins_clean = inf_trips_itins.filter(['date','card_num','trip_id','sch_duration_mins',
                                                'obs_duration_mins','sch_start_time','obs_start_time'])
	inf_trips_itins_clean.columns = inf_trips_itins_clean.columns.str.replace('obs','exec') \
                                                             .str.replace('sch','planned')
	inf_trips_itins_clean['actual_duration_mins'] = inf_trips_itins_clean['exec_duration_mins']
	inf_trips_itins_clean['actual_start_time'] = inf_trips_itins_clean['exec_start_time']
	inf_trips_itins_clean['otp_itinerary_id'] = 0

	inf_trips_itins_clean = inf_trips_itins_clean.filter(['date','trip_id','otp_itinerary_id','planned_duration_mins','actual_duration_mins',
                                     'exec_duration_mins','planned_start_time','actual_start_time','exec_start_time'])

	# Remove scheduled itineraries whose executed trip was not inferred
	sch_obs_trips_itins_clean = sch_obs_trips_itins.filter(['date','trip_id','otp_itinerary_id','sch_duration_mins',
                                                        'obs_duration_mins','sch_start_time','obs_start_time']) \
                                                .merge(inf_trips_itins_clean \
                                                       .filter(['trip_id','exec_duration_mins','exec_start_time']))
	sch_obs_trips_itins_clean.columns = sch_obs_trips_itins_clean.columns.str.replace('sch','planned').str.replace('obs','actual')

	# Merge Datasets
	inef_analysis_base_df = pd.concat([inf_trips_itins_clean,sch_obs_trips_itins_clean], sort=True) \
                            .rename(index=str, columns={'trip_id':'user_trip_id','otp_itinerary_id':'itinerary_id'}) \
                            .filter(['date','user_trip_id','itinerary_id','planned_duration_mins','actual_duration_mins',
                                     'exec_duration_mins','planned_start_time','actual_start_time','exec_start_time']) \
                            .sort_values(['date','user_trip_id','itinerary_id'])

	# Update itinerary_ids
	inef_analysis_base_df['itinerary_id'] = inef_analysis_base_df.groupby(['user_trip_id']).cumcount()	

	# Add itinerary time metadata to support analysis
	inef_analysis_base_df['trip_length_bucket'] = inef_analysis_base_df['exec_duration_mins'].apply(get_trip_len_bucket)
	inef_analysis_base_df['hour_of_day'] = inef_analysis_base_df['exec_start_time'].dt.hour

	period_of_day_list = {'hour_of_day':[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
                      		'period_of_day': ['very_late_night','very_late_night','very_late_night',
                                        'very_late_night','early_morning','early_morning',
                                        'early_morning','morning','morning','morning','morning',
                                        'midday','midday','midday','afternoon','afternoon',
                                        'afternoon','evening','evening','evening','night','night',
                                        'late_night','late_night']}
	period_of_day_df = pd.DataFrame.from_dict(period_of_day_list)
	period_of_day_df.period_of_day = period_of_day_df.period_of_day \
		.astype(pd.api.types.CategoricalDtype(
			categories = ["very_late_night", "early_morning", "morning","midday","afternoon",
					"evening","night","late_night"]))
	inef_analysis_base_df = inef_analysis_base_df.merge(period_of_day_df, how='inner', on='hour_of_day')
	inef_analysis_base_df['weekday'] = inef_analysis_base_df['exec_start_time'].apply(lambda x: x.weekday() < 5)
	inef_analysis_base_df['day_type'] = inef_analysis_base_df['exec_start_time'].apply(get_day_type)

	# Write combined dataset to file
	inef_analysis_base_df.to_csv(output_folderpath + os.sep + file_date_str + '_exec_sch_obs_trips_itins.csv', index=False)
	
	
	
