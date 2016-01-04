#!/usr/bin/env python -*- coding: utf-8 -*-

import os
import re
import sys

import json
import urllib
import urllib3
import logging
import argparse

from arc_eager import arcEager
from ssf_reader import SSFReader
	
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def getAttributeValuePairs(node):
	pairs = list()
	drel_ = list()
	nodeDict = node._asdict()
	for attribute in nodeDict:
		value = nodeDict[attribute]
		if not value: continue
		if attribute == "af": pairs.append("=".join(("af","'%s'" % ",".join([af_attr for af_attr in value]))))
		elif attribute in ["id", "pos", "head"]: pairs.append(value)
		elif attribute in ["drel", "parent"]: drel_.append(value) if attribute == "parent" else drel_.append(value)
		else: pairs.append("=".join((attribute,"'%s'" % value)))
	if drel_: pairs.insert(4, "drel='%s'" % ":".join(drel_))
	return pairs

def backToSSF(tree_, sent_id):
	outputFile.write("%s\n" % sent_id)
	for treelet in tree_:
		if treelet.chunkType == None:
			treelet	= treelet._replace(chunkType="child:%s"%treelet.chunkId)
			treelet = treelet._replace(chunkId=None)
		else:
			for headNode in tree_:
				if headNode.chunkType == None:continue
				if treelet.parent == headNode.chunkId:
					treelet = treelet._replace(parent=headNode.name)
		ssftreelet = getAttributeValuePairs(treelet)
		outputFile.write("\t".join((ssftreelet[0].encode("utf-8"),ssftreelet[1].encode("utf-8"),
			ssftreelet[2].encode("utf-8"), "<fs %s>\n" % " ".join(ssftreelet[3:]).encode("utf-8"))))
	outputFile.write("</Sentence>\n\n")
	logFile.write("%s Successfully expanded!!\n" %sent_id)

def updateHead(head, headinfo, sentence, mapping):
	infoDict = headinfo._asdict()
	for attribute in infoDict:
		if infoDict[attribute] or attribute == "chunkType":
			if attribute == "name": 
				head = head._replace(**{attribute:mapping[int(head.id)]})
			elif attribute == "chunkType":
				head = head._replace(**{attribute:"head:%s" % infoDict['chunkId']})
			elif attribute == "head":
				head = head._replace(**{attribute:head.head})
			elif (headinfo.head != head.name) and (attribute == "af"):continue
			else:
				head = head._replace(**{attribute:infoDict[attribute]})
	if (headinfo.head != head.name) and (head.head != 'NULL'):
		logFile.write("Error: Computed head is probably wrong.\n")
		logFile.write("%s\n" % sentence)
	return head

def ilmtAPI(first, last, text):
        pool = urllib3.PoolManager()
        url = 'http://api.ilmt.iiit.ac.in/hin/pan/%s/%s' % (first, last)
        method = 'POST'
        headers = {'Content-Type':'application/x-www-form-urlencoded', 'charset':'UTF-8'}
        data = pool.urlopen(method, url, headers = headers, body = text).data
        return json.loads(data)

def headVibComputation(sentence):
	#NOTE handled NULL nodes without af
	nullHandled = re.sub(r"<fs name='NULL(.*?)'>",r"<fs af='null,unk,,,,,,' name='NULL\1'>", sentence.strip())
	#NOTE compute head and vibakhti
	headComputed = ilmtAPI('9', '9', "input=%s" % (nullHandled))
	payload = "keep=true&input=" + urllib.quote(headComputed['computehead-9'])
	vibComputed = ilmtAPI('10', '10', payload)["computevibhakti-10"] #NOTE PSPs and Auxillaries are retained.
	return vibComputed

def expander(sentences):
	for idx,sentence in enumerate(sentences):
		sent_id = sentence.group(1).replace("'", '"')
		sentence_content = sentence.group(2)
		sentence = "%s%s</Sentence>" % (sent_id, sentence_content)
		try:
			sentence = headVibComputation(sentence).encode("utf-8")
		except:
			logFile.write("%s -> Error: Something wrong in head or vibhakhti computation\n" % (sent_id))
		logger.info("Sentence number {0} read for processing.".format(idx+1))

		if re.search(r"comment=probsent",sentence):logFile.write("%s -> Error: Found a Probsent comment\n" % (sent_id));continue
		try:
			reader_object = SSFReader(sentence.strip().split("\n")[1:-1]).getAnnotations()
		except:
			logFile.write("%s -> Error: Probably wrong SSF format.\n" % (sent_id));continue
		sanity_check = reader_object.treeSanity()
		if sanity_check:logFile.write("%s -> Error: %s\n" % (sent_id, sanity_check));continue
		tree_ = list()
		for chunk in reader_object.nodeList:
			'''if node.chunkId == "FRAGP":
				tree_.append(getAttributeValuePairs(node, chunkToWordMapping))
				for child in node.children:
					tree_.append(getAttributeValuePairs(child,chunkToWordMapping,(node.name, 'mod')))
				continue'''
			sr_parser = arcEager(grammar, chunk[1:])
			try:
				sr_parser.parse()
			except:
				unknownRule = [" ".join((cn.id,cn.head,cn.pos)) for cn in chunk[1:]]
				logFile.write("Error: Unknown derivation %s\n" % ("|".join(unknownRule).encode("utf-8")))
				logFile.write("%s\n" % sentence)
				tree_ = list()
				break
			expandedChunk = sr_parser.sequence
			expandedChunk[sr_parser.stack[0]] = updateHead(expandedChunk[sr_parser.stack[0]], chunk[0], 
									sentence, reader_object.nodeIndex)
			for node_ in expandedChunk: tree_.append(node_)
		if tree_:backToSSF(tree_, sent_id)
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
	
	filePath = os.path.abspath(args.input)
	logFile.write(filePath+"\n")

	with open(args.grammar) as jfp: grammar = eval(jfp.read())#json.load(jfp)
	with open(args.input) as inputFile:
		inputFileString = inputFile.read()
		sentences = re.finditer("(<Sentence id=.*?>)(.*?)</Sentence>", inputFileString, re.S)
	expander(sentences)
