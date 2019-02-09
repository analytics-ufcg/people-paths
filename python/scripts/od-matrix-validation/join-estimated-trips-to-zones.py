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
MIN_NUM_ARGS = 7

#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <est_trips_folderpath> <output_folder_path> <zones_shapefile_path> <zones_metadata_filepath> <initial_date> <final_date>")

def select_input_files(base_folderpath,init_date,fin_date):
        selected_files = []
        all_files = glob.glob(os.path.join(base_folderpath,"*"))

        for file_ in all_files:
                file_date_str = file_.split('/')[-1].replace('_full_od_trips.csv','')
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

est_trips_folderpath = sys.argv[1]
output_folder_path = sys.argv[2]
zones_shapefile_path = sys.argv[3]
zones_metadata_filepath = sys.argv[4]
initial_date = sys.argv[5]
final_date = sys.argv[6]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

selected_files = select_input_files(est_trips_folderpath,initial_date_dt,final_date_dt)

#Processing files
for file_path,file_date in selected_files:
	
	print("Processing date: ", file_date)

	# Reading and Preparing Estimated Trips data
	est_trips_data = pd.read_csv(file_path, parse_dates=['start_time','end_time'])

	# Group trip legs into a single record
	est_trips_data['date'] = est_trips_data['start_time'].dt.date
	summarized_trips = est_trips_data.groupby(['cardNum','date','user_trip_id']).agg({'start_time': 'first',
                                                                                  'from_stop_id': 'first',
                                                                                  'from_stop_lat': 'first',
                                                                                  'from_stop_lon': 'first',
                                                                                  'end_time': 'last',
                                                                                  'to_stop_id': 'last',
                                                                                  'to_stop_lat': 'last',
                                                                                  'to_stop_lon': 'last'}) \
                                .reset_index()

	# Performing spatial join between the trips origin/destination locations and the city zones
	# Reading and Preparing Zones data
	
	# Reading Zones Shape data
	zones_shp = fix_col_names(geopandas.GeoDataFrame.from_file(zones_shapefile_path))
	
	# Reading Zones Metadata 
	zones_df = fix_col_names(pd.read_csv(zones_metadata_filepath))
	zones_clean = zones_df.filter(['codigo_zoneamento','codigo_macrozona','nm_municip']).drop_duplicates() \
                    .rename(index=str, columns={'codigo_zoneamento':'cod_zona','codigo_macrozona':'cod_macrozona','nm_municip':'municipio'})
	
	# Removing unneeded zones (roads/out-of-bounds)
	zones_clean = zones_clean[zones_clean['cod_zona'] < 1200]

	# Joining Zones Shape and Metadata
	zones_data = zones_shp.merge(zones_clean, left_on='codigo_zon',right_on='cod_zona') \
                        .filter(['cod_zona','cod_macrozona','municipio','densidade_','geometry'])
	
	# Spatially Joining Estimated Trips and Zones data based on origin and destination zone location
	# Transforming Trips dataframe into a geo dataframe
	summarized_trips['from_loc'] = list(zip(summarized_trips.from_stop_lon, summarized_trips.from_stop_lat))
	summarized_trips['to_loc'] = list(zip(summarized_trips.to_stop_lon, summarized_trips.to_stop_lat))

	summarized_trips['from_loc'] = summarized_trips['from_loc'].apply(geom.Point)
	summarized_trips['to_loc'] = summarized_trips['to_loc'].apply(geom.Point)

	trips_od_gdf = geopandas.GeoDataFrame(summarized_trips, geometry='from_loc', crs=zones_data.crs)
	
	# Performing spatial join operation
	trips_od_zones = geopandas.sjoin(trips_od_gdf, 
                                        zones_data.add_suffix('_o').rename(index=str,columns={'geometry_o':'geometry'}),
                                        how='left',
                                        op='within') \
                                .drop('index_right', axis=1)
	trips_od_zones = geopandas.sjoin(trips_od_zones.set_geometry('to_loc'),
                                 zones_data.add_suffix('_d').rename(index=str,columns={'geometry_d':'geometry'}),
                                            how='left',
                                            op='within') \
                                .drop('index_right', axis=1)

	# Building final trips-zones dataset
	trips_od_zones_clean = trips_od_zones.drop(['from_loc','to_loc'], axis=1)	
	
	# Saving final trips-zones dataset to file
	trips_od_zones_clean.to_csv(output_folder_path + os.sep + file_date + '_trips_zones.csv', index=False)


print("Finishing script...")

sys.exit(0)
		
	
