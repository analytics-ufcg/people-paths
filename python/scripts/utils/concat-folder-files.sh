#!/bin/bash


if [ "$#" -lt 2 ]; then
    echo "Wrong number of parameters"
	echo "Usage:"
	echo "./concat-folder-files.sh <input-folderpath> <output-filename>"

else

	input_folderpath=$1
	output_filename=$2

	input_foldername=${input_folderpath##*/}
	random_file=`ls $input_folderpath | shuf -n 1`
	files_header=`head -1 $input_folderpath/$random_file`
	
	output_filepath=$input_folderpath/../$output_filename
	echo $files_header > $output_filepath		

	for f in $input_folderpath/*
	do
		filename=${f##*/} # will drop begin of string upto last occur of `SubStr`
		echo "Processing file: $filename"
		tail -q -n +2 $f >> $output_filepath
	done

	echo "Done!"

fi
