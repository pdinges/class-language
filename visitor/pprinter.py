# -*- coding: utf-8 -*-

# Copyright (c) 2008--2012  Peter Dinges <pdinges@acm.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from visitor import Visitor
from constructs import Sequence

class PrettyPrintVisitor(Visitor):
	"""
	Print AST as nicely indented source code.
	
	Note that the visitor only generates an internal string when traversing
	an AST; it does not output anything by itself.  Use its __str__()
	method to print the code, for example by using "print pv" if pv is a
	PrettyPrintVisitor instance.
	"""
	def __init__(self):
		self.__indentionlist = []
		self.__result = ""
	
	def __indent(self, prefix="  "):
		self.__indentionlist.append(prefix)
	
	def __unindent(self):
		self.__indentionlist.pop()
	
	def __indention(self):
		return "".join(self.__indentionlist)
	
	def __print(self, x):
		self.__result += x
	
	def __printEnclosed(self, pre, obj, post):
		"""
		Shortcut for visiting obj while printing a pre- and postfix.
		"""
		self.__print(pre)
		obj.accept(self)
		self.__print(post)
	
	def __printList(self, l):
		"""
		Shortcut for printing lists of names in parentheses, for
		example argument lists.
		"""
		self.__print("(")
		if l:
			for x in l[:-1]: self.__printEnclosed("", x, ", ")
			l[-1].accept(self)
		self.__print(")")
	
	def __str__(self):
		return self.__result
	
	
	def visitName(self, name):
		self.__print(name.name)
	
	def visitVariable(self, var):
		self.__print(var.name)
	
	
	def visitBoolEq(self, b):
		b.var1.accept(self)
		self.__print(" = ")
		b.var2.accept(self)
	
	def visitBoolNeq(self, b):
		b.var1.accept(self)
		self.__print(" != ")
		b.var2.accept(self)
	
	
	def visitVarExpression(self, varexpr):
		varexpr.var.accept(self)
	
	def visitNew(self, new):
		self.__print("new ")
		new.className.accept(self)
		self.__printList(new.arguments)
	
	def visitCall(self, call):
		call.target.accept(self)
		self.__print(".")
		call.methodName.accept(self)
		self.__printList(call.arguments)

	def visitAssign(self, ass):
		ass.target.accept(self)
		self.__print(" := ")
		ass.rhs.accept(self)
	
	def visitSkip(self, skip):
		self.__print("skip")
	
	def visitReturn(self, ret):
		self.__print("return ")
		ret.var.accept(self)

	def visitSequence(self, seq):
		# Insert semicolons only between statements.
		for S in seq.statements[:-1]:
			self.__printEnclosed(self.__indention(), S, ";\n")
		if seq.statements:
			self.__printEnclosed(self.__indention(), seq.statements[-1], "\n")

	def visitBlock(self, block):
		self.__print("begin\n")
		self.__indent()
		
		for x in block.declaredVars:
			self.__printEnclosed(self.__indention(), x, "\n")
		
		if block.declaredVars and block.sequence.statements:
			self.__print("\n")
		
		block.sequence.accept(self)
		
		self.__unindent()
		self.__print("%send" % self.__indention())
	
	def visitIfThenElse(self, ite):
		self.__printEnclosed("if ", ite.bool, " then\n")
		self.__indent()
		
		self.__printEnclosed(self.__indention(), ite.trueStatement, "")
		
		self.__unindent()
		self.__print("\n%selse\n" % self.__indention())
		self.__indent()
		
		self.__printEnclosed(self.__indention(), ite.falseStatement, "")
		self.__unindent()

	def visitWhile(self, whil):
		self.__printEnclosed("while ", whil.bool, " do ")
		whil.bodyStatement.accept(self)

	def visitVariableDeclaration(self, dv):
		self.__printEnclosed("var ", dv.var, ";")
	
	def visitMethodDeclaration(self, dm):
		self.__printEnclosed("method ", dm.methodName, "")
		self.__printList(dm.parameters)
		self.__printEnclosed(" is ", dm.body, ";")

	def visitConstructorDeclaration(self, dctor):
		self.__print("constructor")
		self.__printList(dctor.parameters)
		self.__printEnclosed(" is ", dctor.body, ";")

	def visitClassDeclaration(self, dc):
		self.__printEnclosed("class ", dc.className, " is begin\n")
		self.__indent()
		
		for x in dc.memberVars:
			self.__printEnclosed(self.__indention(), x, "\n")
		# Separate variable declarations with an empty line.
		if dc.memberVars:
			self.__print("\n")
		
		self.__printEnclosed(self.__indention(), dc.constructor, "\n")
		
		for m in dc.methods:
			self.__printEnclosed("\n%s" % self.__indention(), m, "\n")
		
		self.__unindent()
		self.__print("%send;" % self.__indention())
	
	def visitProgram(self, prog):
		for dc in prog.classDeclarations:
			self.__printEnclosed(self.__indention(), dc, "\n\n")
		self.__printEnclosed("", prog.initialStatement, "\n")

	def visitBlockScopedStatement(self, B):
		if type(B.body) == Sequence:
			self.__print("{\n")
			self.__indent()
			B.body.accept(self)
			self.__unindent()
			self.__print("%s}" % self.__indention())
		else:
			self.__printEnclosed("{ ", B.body, " }")

	def visitMethodScopedStatement(self, B):
		if type(B.body) == Sequence:
			self.__print("[\n")
			self.__indent()
			B.body.accept(self)
			self.__unindent()
			self.__print("%s]" % self.__indention())
		else:
			self.__printEnclosed("[ ", B.body, " ]")
