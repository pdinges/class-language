# $Id$

class Visitor(object):
	"""
	A visitor for abstract syntax trees of Constructs; see there.
	
	Note that the visitor is by itself responsible for tree traversion.
	"""
	def visitName(self, name): pass
	def visitVariable(self, var): pass
	
	def visitBoolEq(self, beq): pass
	def visitBoolNeq(self, bneq): pass
	
	def visitVarExpression(self, varexpr): pass
	def visitNew(self, new): pass
	def visitCall(self, call): pass

	def visitAssign(self, ass): pass
	def visitSkip(self, skip): pass
	def visitReturn(self, ret): pass
	def visitBlock(self, block): pass
	def visitIfThenElse(self, ite): pass
	def visitWhile(self, whil): pass

	def visitVariableDeclaration(self, dv): pass
	def visitMethodDeclaration(self, dm): pass
	def visitClassDeclaration(self, dc): pass

	def visitSequence(self, seq): pass
	def visitBlockScopedStatement(self, B): pass
	def visitMethodScopedStatement(self, B): pass

	def visitProgram(self, prog): pass
