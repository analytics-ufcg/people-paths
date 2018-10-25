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
    print("Usage: " + sys.argv[0] + " <ticketing-base-folder-path> <output-folder-path> <initial-date> <final-date>")

def select_input_files(ticketing_base_path,init_date,fin_date):
	selected_files = []
	all_files = glob.glob(os.path.join(ticketing_base_path,"*"))

	for file_ in all_files:
		file_date_str = file_.split('/')[-1].replace('doc1-','').replace('.csv','')
		file_date = pd.to_datetime(file_date_str,format='%Y_%m_%d') 
		if (file_date >= init_date) and (file_date <= fin_date):
			selected_files.append((file_,file_date))

	return sorted(selected_files)

def get_correct_boarding_data_filepath(ticketing_date,ticketing_base_path):
	boarding_date = ticketing_date + pd.DateOffset(days=1)
	boarding_file = ticketing_base_path + os.sep + 'doc1-' + boarding_date.strftime('%Y_%m_%d') + '.csv'

	return boarding_file

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

ticketing_base_folder_path = sys.argv[1]
output_folder_path = sys.argv[2]
initial_date = sys.argv[3]
final_date = sys.argv[4]

initial_date_dt = pd.to_datetime(initial_date,format='%Y-%m-%d')
final_date_dt = pd.to_datetime(final_date,format='%Y-%m-%d')

selected_files = select_input_files(ticketing_base_folder_path,initial_date_dt,final_date_dt)

#Reading Boarding Data
for file_path,file_date in selected_files:
#	file_date =  pd.to_datetime(file_path.split('/')[-1].split('-')[-1],format='%Y_%m_%d')

	print("Processing date:", file_date.strftime('%Y-%m-%d'))
	#Reading Ticketing Data
	ticketing_data = pd.read_csv(file_path)

	#Preparing dataset
	ticketing_data['boarding_datetime'] = pd.to_datetime(ticketing_data['DATAUTILIZACAO'] + ' ' + ticketing_data['HORAUTILIZACAO'],format='%d/%m/%y %H:%M:%S')
	ticketing_data = ticketing_data.rename(index=str, columns={'CODLINHA': 'route', 
		                                  'CODVEICULO': 'busCode', 
		                                  'DATANASCIMENTO':'birthdate',
		                                  'NOMELINHA':'lineName',
		                                  'NUMEROCARTAO':'cardNum',
		                                  'SEXO':'gender',
		                                  'STOP_ID':'stopPointId'}) \
					.drop(['DATAUTILIZACAO','HORAUTILIZACAO'], axis=1)

	#Indexing Data
	indexed_ticketing = ticketing_data.sort_values(by='boarding_datetime') \
		                            .reset_index(drop=True) \
		                            .reset_index() \
		                            .rename(index=str, columns={'index':'boarding_id'})

	indexed_ticketing_filepath = output_folder_path + os.sep + (file_date - pd.DateOffset(days=1)).strftime('%Y-%m-%d') + '_indexed_ticketing.csv' 

	indexed_ticketing.to_csv(indexed_ticketing_filepath, index=False)

print("Finishing Script...")

sys.exit(0)
