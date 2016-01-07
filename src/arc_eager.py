#!/usr/env python

class arcEager(object):
	
	def __init__(self, grammar, sequence):
		self.stack = list()
		self.template = grammar
		self.sequence = sequence
		self.queue = range(len(sequence))# + [len(sequence)] #NOTE with dummy ROOT

	def isFinalState(self):
		"""
		Checks if the parser is in final configuration i.e. only root node is left in the stack (dummy root not considered)
		"""
		return (len(self.stack) == 1 and len(self.queue) == 0)

	def parse(self):
		"""
		Parses the sequence incrementaly till all the input is consumed and only root node is left.
		"""
		while not self.isFinalState():
			next_move, label = self.predict()
			next_move(label)
		return self

	def predict(self):
		"""
		Predicts the next transition for the parser based on a hand crafted grammar.
		"""	
		if len(self.stack) == 0: 
			return self.SHIFT, None
	
		elif len(self.queue) == 0:
			return self.REDUCE, None	
		else:
			s0 = self.sequence[self.stack[-1]]
			b0 = self.sequence[self.queue[0]]
			if s0.pos in self.template["LEFTARC"] and b0.pos in self.template["LEFTARC"][s0.pos].get("exception", {}):
			        if len(self.queue) == 1: return self.LEFTARC, self.template["LEFTARC"][s0.pos]["exception"][b0.pos]
			        else: return self.SHIFT, None
			elif s0.pos in self.template["LEFTARC"] and (b0.pos in self.template["LEFTARC"][s0.pos].get("norm",{}) or \
			                                                        b0.pos in self.template["LEFTARC"][s0.pos]):
				if not s0.parent:
			        	label = self.template["LEFTARC"][s0.pos].get("norm",{}).get(b0.pos) or \
										self.template["LEFTARC"][s0.pos][b0.pos]
				        return self.LEFTARC, label
				else:
					if b0.pos in self.template["RIGHTARC"] and s0.pos in self.template["RIGHTARC"][b0.pos]:
					        return self.RIGHTARC , self.template["RIGHTARC"][b0.pos][s0.pos]
					elif self.dependencyLink(b0): 
						return self.REDUCE, None
					else: return self.SHIFT, None
			elif b0.pos in self.template["RIGHTARC"] and s0.pos in self.template["RIGHTARC"][b0.pos]:
			        return self.RIGHTARC , self.template["RIGHTARC"][b0.pos][s0.pos]
			elif self.dependencyLink(b0): 
				return self.REDUCE, None
			else: return self.SHIFT, None

	def dependencyLink(self, b0):
		"""
		Resolves ambiguity between shift and reduce actions.
		if a dependency exits between any node (<s0) and (b0) then reduce else shift.
		"""
		for s in self.stack[:-1]:
			sN = self.sequence[s]
			if sN.pos in self.template["LEFTARC"] and b0.pos in self.template["LEFTARC"][sN.pos].get("exception", {}):return True
			if sN.pos in self.template["LEFTARC"] and (b0.pos in self.template["LEFTARC"][sN.pos].get("norm",{}) or \
                                                                                b0.pos in self.template["LEFTARC"][sN.pos]): return True
			if b0.pos in self.template["RIGHTARC"] and sN.pos in self.template["RIGHTARC"][b0.pos]: return True
		return False
			
	def SHIFT(self, label=None):
		"""
		Moves the input from buffer to stack.
		"""
		self.stack.append(self.queue.pop(0))

	def RIGHTARC(self, label=None):
		"""
		Right reduces the tokens at the buffer and stack.
		"""
		s0 = self.stack[-1]
		b0 = self.queue.pop(0)
		self.stack.append(b0)
		self.sequence[b0] = self.sequence[b0]._replace(drel=label)
		self.sequence[b0] = self.sequence[b0]._replace(parent=self.sequence[s0].name)

	def LEFTARC(self, label=None):
		"""
		Left reduces the tokens at the stack and buffer.
		"""
		s0 = self.stack.pop()
		b0 = self.queue[0]
		self.sequence[s0] = self.sequence[s0]._replace(drel=label)
		self.sequence[s0] = self.sequence[s0]._replace(parent=self.sequence[b0].name)

	def REDUCE(self, label=None):
		"""
		Pops the top of the stack, if it has been attached to a word.
		"""
		self.stack.pop()
