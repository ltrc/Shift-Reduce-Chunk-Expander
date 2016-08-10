#!/usr/bin/env bash

if [[ $# -ne 4 ]]
then
	echo "Required arguments not provided! Exiting now .. .. .."
	echo "USAGE: bash run_expander.sh <input[file|folder]> <output file> <grammar> <language>"
	exit
fi

if [[ -f log ]]
then
	rm log
fi

input=$1
output=$2
grammar=$3
language=$4

if [[ -f $input ]]
then
	python chunk_expander.py --input $1 --output $output --log log --grammar $grammar --lang $language
elif [[ -d $input ]]
then
	for file in $(find $input -name '*' );
	do
		if [[ -f $file ]]
		then
			python chunk_expander.py --input $file --output $file.exp --log log --grammar $grammar --lang $language
			mv $file.exp $file
		fi
	done
else
	echo "Input neither of type file nor directory. Exiting now .. .. .."
fi
