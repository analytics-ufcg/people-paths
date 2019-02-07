#!/bin/bash


if [ "$#" -lt 2 ]; then
    echo "Wrong number of parameters"
	echo "Usage:"
	echo "./concat-hdfs-output-parts.sh <input-folderpath> <output-folderpath>"

else

	input_folderpath=$1
	output_folderpath=$2

	for f in $input_folderpath/*
	do
		subfoldername=${f##*/} # will drop begin of string upto last occur of `SubStr`
		echo "Processing date: $subfoldername - located at: $f"
		output_subfolderpath=$output_folderpath/$subfoldername.csv
		
		files_header=`head -1 $f/part-00000`
		
		echo $files_header > $output_subfolderpath		
		tail -q -n +2 $f/part-* >> $output_subfolderpath
	done

	echo "Done!"

fi
