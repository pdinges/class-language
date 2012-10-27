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
