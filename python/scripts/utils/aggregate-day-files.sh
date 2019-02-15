#!/bin/bash


if [ "$#" -lt 3 ]; then
    echo "Wrong number of parameters"
	echo "Usage:"
	echo "./aggregate-day-files.sh <input-folderpath> <output-folderpath> <output-file-suffix>"

else

	input_folderpath=$1
	output_folderpath=$2
	output_filesuffix=$3

	random_file=`ls $input_folderpath | shuf -n 1`
	files_header=`head -1 $input_folderpath/$random_file`
	#echo $random_file
	#echo $files_header
	final_file_suffix="_full_"
	#filesuffix=${random_file: -12}
	dates=()

	for f in $input_folderpath/*
	do
		filename=${f##*/} # will drop begin of string upto last occur of `SubStr`
		filedate=${filename:0:10}
		filedate_regex="$input_folderpath/$filedate"
		dates+=("$filedate_regex")
	done

	unique_dates=($(for v in "${dates[@]}"; do echo "$v";done| sort -u))
	#echo "${unique_dates[@]}"

	for file_date in "${unique_dates[@]}"
	do
		echo "Base date:" $file_date
		filedate=${file_date##*/}
		final_filepath="$output_folderpath/$filedate$final_file_suffix$output_filesuffix"
		echo "Full Data Filepath:" $final_filepath
		echo $files_header > tmp.csv
		tail -q -n +2 $file_date* >> tmp.csv
		cat tmp.csv > $final_filepath
		rm tmp.csv
	done 

	echo "Done!"

fi
