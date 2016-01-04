#!/usr/bin/env bash

if [[ $# -ne 3 ]]
then
	echo "Required arguments not provided! Exiting now .. .. .."
	echo "USAGE: bash run_expander.sh <input[file|folder]> <output file> <grammar>"
	exit
fi

if [[ -f log ]]
then
	rm log
fi

input=$1
output=$2
grammar=$3

if [[ -f $input ]]
then
	python chunk_expander.py --input $1 --output $output --log log --grammar $grammar
elif [[ -d $input ]]
then
	for file in $(find $input -name '*' );
	do
		if [[ -f $file ]]
		then
			python chunk_expander.py --input $file --output $output --log log --grammar $grammar
		fi
	done
else
	echo "Input neither of type file nor directory. Exiting now .. .. .."
fi
