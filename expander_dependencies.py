#!/usr/bin/env python -*- coding:utf-8 -*-
import re
import sys
import tempfile
import commands

def run_dependencies(ssfSentences, sentencIds):

	vibPath = "$ssf2conll/dependencies/vibhakticomputation/"
	headPath = "$ssf2conll/dependencies/headcomputation-1.8/"
	
	for idx, sentence in enumerate(ssfSentences):
		sentence = re.sub(r"<fs name='NULL(.*?)'>",r"<fs af='null,unk,,,,,,' name='NULL\1'>",\
			   '<Sentence id="'+str(sentencIds[idx])[1:-1]+'">\n'+sentence.strip()+"\n</Sentence>\n") 
			   # add af='' to null nodes.
		tempInput = tempfile.NamedTemporaryFile()
		tempOutput = tempfile.NamedTemporaryFile()
		try:
			tempInput.write(sentence)
			tempInput.seek(0)
			head=commands.getstatusoutput(\
				"ulimit -t 20;sh "+" "+ headPath+"headcomputation_run.sh "+" " + tempInput.name)
			tempOutput.write(head[-1])
			tempOutput.seek(0)
			vib=commands.getstatusoutput(\
				"ulimit -t 20;sh "+" "+ vibPath+"vibhakticomputation_run.sh " + " " + tempOutput.name)
			yield vib[-1]
		finally:
			tempInput.close()
			tempOutput.close()
