#!/usr/env python

import json

class arcEager(object):
	
	def __init__(self, grammar):
		self.stack = list()
		self.template = grammar
		self.sequence = sequence
		self.labeledEdges = list()
		self.queue = range(len(sequence))# + [len(sequence)] #NOTE with dummy ROOT

	def isFinalState(self):
		"""
		Checks if the parser is in final configuration i.e. only root node is left in the stack (dummy root not considered)
		"""
		return (len(self.stack) == 1 and len(self.queue) == 0)

	def parse(self, sequence):
		"""
		Parses the sequence incrementaly till all the input is consumed and only root node is left.
		"""
		while not self.isFinalState():
			next_move, label = self.nextTransition()
			next_move(label)
		return self

	def nextTransition(self):
		"""
		Predicts the next transition for the parser based on a hand crafted grammar.
		"""	
		if len(self.stack) == 0: 
			return self.SHIFT, None
		
		else:
			s0 = self.sequence[self.stack[-1]]
			b0 = self.sequence[self.queue[0]]
			#if s0.pos in self.template and b0.pos in self.template[s0.pos][0]: return self.LEFTARC, self.template[s0.pos][-1]
			#elif b0.pos in self.template and s0.pos in self.template[b0.pos][0]: return self.RIGHTARC , self.template[b0.pos][-1]
			if s0.pos in self.template["LEFTARC"] and b0.pos in self.template["LEFTARC"][s0.pos][0]: 
				return self.LEFTARC, self.template["LEFTARC"][s0.pos][-1]
			elif b0.pos in self.template["RIGHTARC"] and s0.pos in self.template["RIGHTARC"][b0.pos][0]: 
				return self.RIGHTARC , self.template["RIGHTARC"][b0.pos][-1]
			else: return self.SHIFT, None

	def SHIFT(self, label=None):
		"""
		Moves the input from buffer to stack.
		"""
		self.stack.append(self.queue.pop(0))
		return self

	def RIGHTARC(self, label=None):
		"""
		Right reduces the tokens at the buffer and stack.
		"""
		s0 = self.stack[-1]
		b0 = self.queue.pop(0)
		#self.stack.append(b0)
		self.labeledEdges.append((self.sequence[b0], (self.sequence[s0].name, label)))
		return self

	def LEFTARC(self, label=None):
		"""
		Left reduces the tokens at the stack and buffer.
		"""
		s0 = self.stack.pop()
		b0 = self.queue[0]
		self.labeledEdges.append((self.sequence[s0], (self.sequence[b0].name,label)))
		return self

	def REDUCE(self):
		"""
		This thing is never called!
		"""
		self.stack.pop()
		return self
