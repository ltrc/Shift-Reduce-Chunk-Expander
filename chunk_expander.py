#!/usr/bin/env python -*- coding: utf-8 -*-

import os
import re
import sys

import logging
import argparse

from ssf_reader import SSFReader
from shift_reduce_parser import arcEager
from expander_dependencies import run_dependencies as RD
	
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

afAttributes = ('lemma','cat','gen','num','per','case','vib','tam')
allAttributes = ('id', 'head','pos','poslcat','af','vpos','name','drel','parent','chunkId','chunkType',
								'mtype','troot', 'coref','stype','voicetype','posn')
def getAttributeValuePairs(node, mapping, label=None):
	pairs = list()
	drel_ = list()
	#print node
	for attribute in allAttributes:
		value = eval('node.'+attribute)
		if not value: continue	
		if attribute == "af": pairs.append("=".join(("af","'%s'" % ",".join([af_attr for af_attr in value]))))
		elif attribute in ["id", "pos", "head"]: pairs.append(value)
		elif attribute in ["drel", "parent"]: 
			if label: drel_.append(label[0]) if attribute == "parent" else drel_.append(label[-1])
			else: drel_.append(mapping[value]) if attribute == "parent" else drel_.append(value)
		else: pairs.append("=".join((attribute,"'%s'" % value)))
	if drel_: pairs.insert(4, "drel='%s'" % ":".join(drel_))
	return pairs

def expander(sentences):
	for idx,sentence in enumerate(sentences):
		logger.info("Sentence number {0} read for processing.".format(idx+1))
		if re.search(r"comment=probsent", sentence):
			logFile.write("<Sentence id="+str(sentence_ids[idx])+">"+"#Found a Probsent comment\n")
		elif re.search(r"</Sentence>", sentence):
			try:
				reader_object = SSFReader(sentence.strip()).getAnnotations()
			except:
				logFile.write("<Sentence id="+sentence_ids[idx]+">"+" Error#Probably wrong SSF format.\n")
				continue
			sanity_check = reader_object.treeSanity()
			if sanity_check:
				logFile.write("<Sentence id="+sentence_ids[idx]+">"+" Error%s\n" % sanity_check)
				continue
			chunkToWordMapping = reader_object.chunk_word
			tree_ = list()
			#for n in reader_object.nodeList:print n
			for node in reader_object.nodeList:
				if node.children:
					if node.chunkId == "FRAGP":
						tree_.append(getAttributeValuePairs(node, chunkToWordMapping))
						for child in node.children:
							tree_.append(getAttributeValuePairs(child,chunkToWordMapping,(node.name, 'mod')))
						continue
					try:
						sr_parser.parse(sorted([node]+node.children, key=lambda node_: int(node_.id)))
					except:
						unknownRule = [" ".join((node.id,node.head,node.pos))]+[" ".join((i.id,i.head,i.pos)) \
														for i in node.children]
						logFile.write("<Sentence id="+sentence_ids[idx]+">"+\
							" Error#Unknown derivation %s\n" % "|".join(unknownRule).encode("utf-8"))
						logFile.write("%s\n" % sentence)
						break	
					labeledChildren = sr_parser.labeledEdges
					# head computed by headcomputation module and by the shift reduce parser aren't same.
					if sr_parser.sequence[sr_parser.stack[0]].name != node.name:
						logFile.write("<Sentence id="+sentence_ids[idx]+">"+\
							" Error#Computed head is probably wrong.\n")
						logFile.write("%s\n" % sentence)
						break	
					for child,label_ in labeledChildren:
						tree_.append(getAttributeValuePairs(child,chunkToWordMapping,label_))
					tree_.append(getAttributeValuePairs(node, chunkToWordMapping))
				else: tree_.append(getAttributeValuePairs(node, chunkToWordMapping))
			else:
				#continue
				tree_ = sorted(tree_, key=lambda id_: int(id_[0]))
				outputFile.write("<Sentence id=%s>\n" % sentence_ids[idx])
				for treelet_ in tree_: outputFile.write("\t".join((treelet_[0].encode("utf-8"),treelet_[1].encode("utf-8"),
							treelet_[2].encode("utf-8"), "<fs %s>\n" % " ".join(treelet_[3:]).encode("utf-8"))))
				outputFile.write("</Sentence>\n\n")
				logFile.write("<Sentence id="+sentence_ids[idx]+">"+" Successfully expanded!!\n")
		else: 
			logFile.write("<Sentence id="+str(sentence_ids[idx])+">"+"#Error in head or vibhakhti computation\n")
	
	logFile.close()
	outputFile.close()
		
if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description="Chunk Expander !!")
	parser.add_argument('--input-file'     , dest='input'     , required=True, help='Input file in ssf format')
	parser.add_argument('--output-file'    , dest='output'    , required=True, help='Output file')
	parser.add_argument('--grammar-file'   , dest='grammar'   , required=True, help='Grammar file')
	parser.add_argument('--log-file'       , dest='log'       , required=True, help='will contain expansion details')

	args = parser.parse_args()
	
	if os.path.isfile(os.path.abspath(args.output)): outputFile = open(args.output,'a')
	else: outputFile = open(args.output,'w')
	
	if os.path.isfile(os.path.abspath(args.log)): logFile = open(args.log,'a')
	else: logFile = open(args.log,'w')
	
	inputFile = open(args.input).read()
	
	with open(args.grammar) as jfp: grammar = json.load(jfp)
	
	sr_parser = arcEager(grammar)
 	
	sentence_ids = re.findall('<Sentence id=(.*?)>', inputFile)
	sentences = re.findall("<Sentence id=.*?>(.*?)</Sentence>",inputFile, re.S)
	
	filePath = os.path.abspath(args.input)
	head_vib_computed_sentences = RD(sentences, sentence_ids)

	expander(head_vib_computed_sentences)
