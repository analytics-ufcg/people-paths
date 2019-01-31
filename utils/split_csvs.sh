#!/bin/bash

#sudo apt-get install parallel

if [ "$#" -lt 2 ]; then
    echo "Wrong number of parameters"
	echo "Usage:"
	echo "./split_csvs.sh <input_dir> <num_lines> <output_dir>"

else
	input_dir=$1
	num_lines=$2
	out_dir=$3

	for file in $input_dir/*.csv
	do
		full_filename="${file##*/}"
		filename="${full_filename%.*}"
		echo "Processing $filename"
    	cat $file | parallel --header : --pipe -N $num_lines "cat > ${out_dir}/${filename}_{#}.csv"
	done
fi
