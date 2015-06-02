#!/usr/bin/env bash

if [[ $# -ne 2 ]]
then
	echo "Required arguments not provided! Exiting now .. .. .."
	exit
fi

if [[ -f log ]]
then
	rm log
fi

input=$1
output=$2

if [[ -f $input ]]
then
	python chunk_expander.py --input $1 --output $output --log log
elif [[ -d $input ]]
then
	for file in $(find $input -name '*' );
	do
		if [[ -f $file ]]
		then
			python chunk_expander.py --input $file --output $output --log log
		fi
	done
else
	echo "Input neither of type file nor directory. Exiting now .. .. .."
fi
