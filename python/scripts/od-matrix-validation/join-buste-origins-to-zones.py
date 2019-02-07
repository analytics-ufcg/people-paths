#Libraries

#Python Libs
import sys
import os
import glob

#Data Analysis Libs
import pandas as pd
import numpy as np
import geopandas
import shapely.geometry as geom

#Constants
MIN_NUM_ARGS = 6

#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <buste_origins_folderpath> <output_folder_path> <zones_dataset_filepath> <initial_date> <final_date>")

def select_input_files(base_folderpath,init_date,fin_date):
        selected_files = []
        all_files = glob.glob(os.path.join(base_folderpath,"*"))

        for file_ in all_files:
                file_date_str = file_.split('/')[-1].replace('.csv','')
                file_date = pd.to_datetime(file_date_str,format='%Y_%m_%d')
                if (file_date >= init_date) and (file_date <= fin_date):
                        selected_files.append((file_,file_date_str))

        return sorted(selected_files)

def fix_col_names(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
    return(df)


#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

buste_origins_folderpath = sys.argv[1]
output_folder_path = sys.argv[2]
zones_dataset_filepath = sys.argv[3]
initial_date = sys.argv[4]
final_date = sys.argv[5]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

selected_files = select_input_files(buste_origins_folderpath,initial_date_dt,final_date_dt)

#Processing files
for file_path,file_date in selected_files:
	
        print("Processing date: ", file_date)

        # Reading and Preparing Estimated Trips data
        buste_origins_data = pd.read_csv(file_path, usecols=['cardNum','boarding_datetime','route','stopPointId','shapeLat','shapeLon'],
                                            parse_dates=['boarding_datetime']) \
                                .rename(index=str, columns={'cardNum':'card_num','boarding_datetime':'start_time',
                                    'stopPointId':'from_stop_id','shapeLat':'from_stop_lat','shapeLon':'from_stop_lon'}) \
                                .query('card_num != \'-\'') \
                                .filter(['card_num','route','start_time','from_stop_id','from_stop_lat','from_stop_lon'])
        
        if (len(buste_origins_data) == 0):
            print("There is no boarding data in BUSTE output for this date.")
            continue

        # Reading Zones Metadata
        zones_data = fix_col_names(geopandas.GeoDataFrame.from_file(zones_dataset_filepath))
        
        # Performing spatial join between the trips origin locations and the city zones
	# Transforming Trips dataframe into a geo dataframe
        buste_origins_data['from_loc'] = list(zip(buste_origins_data.from_stop_lon, buste_origins_data.from_stop_lat))
        buste_origins_data['from_loc'] = buste_origins_data['from_loc'].apply(geom.Point)
        trips_o_gdf = geopandas.GeoDataFrame(buste_origins_data, geometry='from_loc', crs=zones_data.crs)
	
        # Performing spatial join operation
        trips_o_zones = geopandas.sjoin(trips_o_gdf, 
                                        zones_data.add_suffix('_o').rename(index=str,columns={'geometry_o':'geometry'}),
                                        how='left',
                                        op='within') \
                                .drop('index_right', axis=1)

	# Building final trips-zones dataset
        trips_o_zones_clean = trips_o_zones.drop(['from_loc'], axis=1)
	
	# Saving final trips-zones dataset to file
        trips_o_zones_clean.to_csv(output_folder_path + os.sep + file_date + '_buste_o_zones.csv', index=False)


print("Finishing script...")

sys.exit(0)
		
	
