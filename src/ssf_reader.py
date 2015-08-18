#!/usr/bin/python -*- coding:utf-8 -*-

__Author__ = "Riyaz Ahmad Bhat"
__Email__ = "riyaz.ah.bhat@gmail.com"


import re
from collections import namedtuple

from sanity_checker import SanityChecker

class DefaultList(list):
    """Equivalent of Default dictionaries for Indexing Errors."""
    def __init__(self, default=None):
        self.default = default
        list.__init__(self)

    def __getitem__(self, index):
        try: return list.__getitem__(self, index)
        except IndexError: return self.default

class SSFReader (SanityChecker):
	
	def __init__ (self, sentence):

		super(SSFReader, self).__init__()
		self.id_ = int()
		self.nodeList = list()
		self.chunk_word = dict()
		self.sentence = sentence
		self.modifierModified = dict()
		self.node = namedtuple('node', 
						('id', 'head', 'children', 'pos', 'poslcat', 'af', 'vpos', 'name','drel','parent',
						'chunkId', 'chunkType', 'mtype', 'troot', 'coref', 'stype','voicetype', 'posn'))
		self.features = namedtuple('features',
							('lemma','cat','gen','num','per','case','vib','tam'))

	def getAnnotations (self):
						
		children_ = list()


		for line in self.sentence.split("\n"):
			nodeInfo = line.decode("utf-8").split("\t")

			if nodeInfo[0].isdigit():
				assert len(nodeInfo) == 4 # no need to process trash! FIXME
				attributeValue_pairs = self.FSPairs(nodeInfo[3][4:-1])
				attributes = self.updateFSValues(attributeValue_pairs)
				h = attributes.get #NOTE h -> head node attributes

			elif nodeInfo[0].replace(".",'',1).isdigit():
				assert (len(nodeInfo) == 4) and (nodeInfo[1] and nodeInfo[2] != '') # FIXME
				self.id_ += 1
				pos_ = nodeInfo[2].encode("utf-8").decode("ascii",'ignore').encode("ascii")
				wordForm_ = nodeInfo[1]
				attributeValue_pairs = self.FSPairs(nodeInfo[3][4:-1])

				if attributeValue_pairs['name'] == h('head_'):# NOTE head word of the chunk
					self.nodeList.append(self.node(str(self.id_),wordForm_,children_,pos_,h('poslcat_'),
						self.features(h('lemma_') if h('lemma_') else wordForm_ ,h('cat_'),h('gen_'), h('num_'),
						h('per_'),h('case_'),h('vib_'),h('tam_')),h('vpos_'),h('head_'),h('drel_'), 
						h('parent_'),h('chunkId_'),":".join(('head',h('chunkId_'))),h('mtype_'),h('troot_'),
						h('coref_'),h('stype_'),h('voicetype_'),h('posn_')))
					self.modifierModified[h('chunkId_')] = h('parent_')
					self.chunk_word[h('chunkId_')] = h('head_')

				else:
					attributes = self.updateFSValues(attributeValue_pairs)
					c = attributes.get #NOTE c -> child node attributes
					children_.append(self.node(str(self.id_),wordForm_,[],pos_,c('poslcat_'),self.features(c('lemma_') \
						if c('lemma_') else wordForm_ ,c('cat_'),c('gen_'),c('num_'),c('per_'),c('case_'),c('vib_'),
						c('tam_')),c('vpos_'),c('name_'),"_","_",None,":".join(('child',h('chunkId_'))),c('mtype_'),
						c('troot_'),c('coref_'),None, None, c('posn_')))

			else: children_ = list()

		return self

	def FSPairs (self, FS) :

		feats = dict()
		for feat in FS.split():
			if "=" not in feat:continue
			feat = re.sub("af='+","af='",feat.replace("dmrel=",'drel='))
			assert len(feat.split("=")) == 2
			attribute,value = feat.split("=")
			feats[attribute] = value

		return feats

	def morphFeatures (self, AF):
		"LEMMA,CAT,GEN,NUM,PER,CASE,VIB,TAM"
		assert len(AF[:-1].split(",")) == 8 # no need to process trash! FIXME
		lemma_,cat_,gen_,num_,per_,case_,vib_,tam_ = AF.split(",")

		if len(lemma_) > 1: lemma_ = lemma_.strip("'")
		return lemma_.strip("'"),cat_,gen_,num_,per_,case_,vib_,tam_.strip("'")
	
	def updateFSValues (self, attributeValue_pairs):

		attributes = dict(zip(['head_','poslcat_','af_','vpos_','name_','drel_','parent_','mtype_','troot_','chunkId_',\
					'coref_','stype_','voicetype_','posn_'], [None] * 14))
		attributes.update(dict(zip(['lemma_','cat_','gen_','num_','per_','case_','vib_','tam_'], [''] * 8)))

		for key,value in attributeValue_pairs.items():
			if key == "af":
				attributes['lemma_'],attributes['cat_'],attributes['gen_'],attributes['num_'],\
				attributes['per_'],attributes['case_'],attributes['vib_'],attributes['tam_'] = \
					self.morphFeatures (value)
			elif key == "drel":
				assert len(value.split(":")) == 2 # no need to process trash! FIXME
				attributes['drel_'], attributes['parent_'] = re.sub("'|\"",'',value).split(":")
				assert attributes['drel_'] and attributes['parent_'] != "" # no need to process trash! FIXME
			else:
				variable = str(key) + "_"
				if variable == "name_": attributes['chunkId_'] = re.sub("'|\"",'',value)
				attributes[variable] = re.sub("'|\"",'',value)
		return attributes
