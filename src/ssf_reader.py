#!/usr/bin/python -*- coding:utf-8 -*-

__Author__ = "Riyaz Ahmad Bhat"
__Email__ = "riyaz.ah.bhat@gmail.com"

import re
from collections import namedtuple

from sanity_checker import SanityChecker

class SSFReader (SanityChecker):
    
    def __init__ (self, sentence):

        self.id_ = int()
        self.nodeList = list()
        self.nodeIndex = dict()
	self.instances = dict()
        self.sentence = sentence
        self.modifierModified = dict()
        self.node = namedtuple('node', 
                        ['id', 'head', 'pos', 'poslcat', 'af', 'vpos', 'name','drel','parent', 'pid',
                        'chunkId', 'chunkType', 'mtype', 'troot', 'coref', 'stype','voicetype', 'posn'])
        self.features = namedtuple('features',
                            ['lemma','cat','gen','num','per','case','vib','tam'])

    def getAnnotations (self):
        children_ = list()
        chunkId = str()
        for line in self.sentence:
            nodeInfo = line.decode("utf-8").split("\t")
            if nodeInfo[0].isdigit(): # chunk
                assert len(nodeInfo) == 4 # no need to process trash! FIXME
                attributeValue_pairs = self.FSPairs(nodeInfo[3][4:-1])
                attributes = self.updateFSValues(attributeValue_pairs)
                c = attributes.get #NOTE h -> head node attributes
                chunkId = c('chunkId_')
                children_.append(self.node._make([None,c('head_'),None,c('poslcat_'),self.features(c('lemma_')\
                    if c('lemma_') else (c('head_') or '') ,c('cat_'),c('gen_'),c('num_'),c('per_'),c('case_'),
                    c('vib_'),c('tam_')),c('vpos_'),c('name_'),c('drel_'),c('parent_'),c('pid_'),c('chunkId_'),
                    None,c('mtype_'),c('troot_'),c('coref_'),c('stype_'),c('voicetype_'),c('posn_')]))
                self.modifierModified[c('chunkId_')] = c('parent_')
            elif nodeInfo[0].replace(".",'',1).isdigit(): # word 
                assert (len(nodeInfo) == 4) and (nodeInfo[1] and nodeInfo[2] != '') # FIXME
                self.id_ += 1
                pos_ = nodeInfo[2].encode("utf-8").decode("ascii",'ignore').encode("ascii")
                wordForm_ = re.sub("'", "`", nodeInfo[1])
		self.instances.setdefault(wordForm_, 0)
		self.instances[wordForm_] += 1
                attributeValue_pairs = self.FSPairs(nodeInfo[3][4:-1], wordForm_)
                attributes = self.updateFSValues(attributeValue_pairs, wordForm_, pos_)
                c = attributes.get #NOTE c -> child node attributes
                self.nodeIndex[self.id_] = c('name_')
                children_.append(self.node._make([str(self.id_),wordForm_,pos_,c('poslcat_'),self.features(c('lemma_')\
                    if c('lemma_') else wordForm_ ,c('cat_'),c('gen_'),c('num_'),c('per_'),c('case_'),c('vib_'),
                    c('tam_')),c('vpos_'),c('name_'),None,None,None,chunkId,None,c('mtype_'),
                    c('troot_'),c('coref_'),None, None, c('posn_')]))
            else: 
                self.nodeList.append(children_)
                children_ = list()
        return self

    def FSPairs (self, FS, terminal=False) :
        feats = dict()
        for feat in FS.split():
            if "=" not in feat:continue
            feat = re.sub("af='+","af='",feat.replace("dmrel=",'drel='))
            assert len(feat.split("=")) == 2
            attribute,value = feat.split("=")
	
	    if (value[0] == value[-1]) and (value[0] in ["'", '"']):
            	value = re.sub("'", "`", value[1:-1])
	    else:
		value = re.sub("'", "`", value)
		
	    if (terminal) and (attribute == "name"):
		icount = self.instances[terminal]
		value = terminal if icount < 2 else "%s%s" % (terminal, icount)

            feats[attribute] = value
		
        return feats

    def morphFeatures (self, AF, word, tag):
        "LEMMA,CAT,GEN,NUM,PER,CASE,VIB,TAM"
        #assert len(AF[:-1].split(",")) == 8 # no need to process trash! FIXME
        if tag == 'SYM':
            lemma_,cat_ = word, 'punc'
            gen_,num_,per_,case_,vib_,tam_ = [''] * 6
        else:   
            lemma_,cat_,gen_,num_,per_,case_,vib_,tam_ = AF.split(",")
        if len(lemma_) > 1: lemma_ = lemma_.strip("'")
        return lemma_.strip("'"),cat_,gen_,num_,per_,case_,vib_,tam_.strip("'")
    
    def updateFSValues (self, attributeValue_pairs, word=None, tag=None):
        attributes = dict(zip(['head_','poslcat_','af_','vpos_','name_','drel_','parent_','pid_','mtype_','troot_','chunkId_',
                    'coref_','stype_','voicetype_','posn_'], [None] * 15))
        attributes.update(dict(zip(['lemma_','cat_','gen_','num_','per_','case_','vib_','tam_'], [''] * 8)))
        for key,value in attributeValue_pairs.items():
            if key == "af":
                attributes['lemma_'],attributes['cat_'],attributes['gen_'],attributes['num_'],\
                attributes['per_'],attributes['case_'],attributes['vib_'],attributes['tam_'] = \
                    self.morphFeatures (value, word, tag)
            elif key == "drel":
                assert len(value.split(":",1)) == 2 # no need to process trash! FIXME
                attributes['drel_'], attributes['parent_'] = re.sub("'|\"","",value).split(":",1)
                assert attributes['drel_'] and attributes['parent_'] != "" # no need to process trash! FIXME
            else:
                variable = "%s_" % str(key)
                if variable == "name_": attributes['chunkId_'] = value.strip("'\"")
                attributes[variable] = value.strip("'")
        return attributes
