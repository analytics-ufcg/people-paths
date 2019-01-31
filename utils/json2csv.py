import csv
import json
import sys
import time
import os
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

MIN_NUM_ARGS = 3

def printUsage():
	#print "Usage: python json2csv.py <input_json_file_path> <input_csv_file_path>"
	print "Usage: python json2csv.py <input_json_file_path> <input_csv_file_path> <type_usage>"
	# exemplo: python json2csv.py arquivo_inicial.json arquivo_final.csv (file|folder)

if (len(sys.argv) < MIN_NUM_ARGS):
	print "Wrong number of parameters."
	printUsage()
	exit(1)


def setJsonToCSV(csvFile, file_path,first_file=True):
	with open(file_path) as f:
		linenum = 0
		json_keys = []
		for line in f:
			if linenum != 0:
				j_content = json.loads(line)
				if linenum == 1:
					# Write CSV Header
					json_keys = j_content.keys()
					if first_file:
						csvFile.writerow(json_keys)
				row = []
				for key in json_keys:
					row.append(j_content[key]) 
				csvFile.writerow(row)
			linenum += 1



input_file_path = sys.argv[1]
output_file_path = sys.argv[2]
type_usage = sys.argv[3]

if (type_usage != "path" and type_usage != "file"):
	print "type_usage: path/file"
	exit(1)


start_time = time.time()

csvFile = csv.writer(open(output_file_path, "wb+"))

if (type_usage == "file"):
	setJsonToCSV(csvFile, input_file_path)
elif (type_usage == "path"):
	first_file = True
	for file in os.listdir(input_file_path):
		if file.endswith(".txt"):
			setJsonToCSV(csvFile, input_file_path+file, first_file)
			first_file = False

print("--- Processing took %s seconds ---" % (time.time() - start_time))
