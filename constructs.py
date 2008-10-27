# $Id$

# ==========
# Constructs
# ==========
#
# We represent constructs of syntax rules as instances of respective classes.
# Because the syntax rules use constructs of other rules as building blocks,
# the constructs form a tree.  This abstract syntax tree (AST) is our internal
# representation of the program.
#
# We employ the visitor design pattern to separate algorithms that work on the
# AST from the AST's representation: each construct (that is, node in the AST)
# has a method accept() that calls a method in the visitor, depending on the
# construct's type.
#
# See chapter 2 in the thesis for a list of syntax rules; the syntactic
# categorys of these rules imply all classes in this module (and their design).

class Construct(object):
	def accept(self, visitor): pass
	def copy(self): return Construct()

class Name(Construct):
	def __init__(self, n): self.name = n
	def accept(self, visitor): visitor.visitName(self)
	def copy(self): return Name(self.name)

class Variable(Construct):
	def __init__(self, v): self.name = v
	def accept(self, visitor): visitor.visitVariable(self)
	def copy(self): return Variable(self.name)


class Bool(Construct): pass

class BoolEq(Bool):
	def __init__(self, y1, y2):
		self.var1 = y1
		self.var2 = y2
	def accept(self, visitor): visitor.visitBoolEq(self)
	def copy(self): return BoolEq(self.var1.copy(), self.var2.copy())

class BoolNeq(Bool):
	def __init__(self, y1, y2):
		self.var1 = y1
		self.var2 = y2
	def accept(self, visitor): visitor.visitBoolNeq(self)
	def copy(self): return BoolNeq(self.var1.copy(), self.var2.copy())


class Expression(Construct): pass

class VarExpression(Expression):
	def __init__(self, y):
		self.var = y
	def accept(self, visitor): visitor.visitVarExpression(self)
	def copy(self): return VarExpression(self.var.copy())

class New(Expression):
	def __init__(self, c, a):
		self.className = c
		if a:
			self.arguments = a
		else:
			self.arguments = []
	def accept(self, visitor): visitor.visitNew(self)
	def copy(self): return New(self.className.copy(), self.arguments[:])

class Call(Expression):
	def __init__(self, y, m, a):
		self.target = y
		self.methodName = m
		if a:
			self.arguments = a
		else:
			self.arguments = []
	def accept(self, visitor): visitor.visitCall(self)
	def copy(self):
		return Call(
			self.target.copy(),
			self.methodName.copy(),
			self.arguments[:]
		)


class Statement(Construct): pass

class Assign(Statement):
	def __init__(self, x, rhs):
		self.target = x
		self.rhs = rhs
	def accept(self, visitor): visitor.visitAssign(self)
	def copy(self): return Assign(self.target.copy(), self.rhs.copy())

class Skip(Statement):
	def accept(self, visitor): visitor.visitSkip(self)
	def copy(self): return Skip()

class Return(Statement):
	def __init__(self, y):
		self.var = y
	def accept(self, visitor): visitor.visitReturn(self)
	def copy(self): return Return(self.var.copy())

class Sequence(Construct):
	def __init__(self, SS):
		self.statements = SS
	def accept(self, visitor): visitor.visitSequence(self)
	def copy(self): return Sequence(self.statements[:])

class Block(Statement):
	def __init__(self, dv, Q):
		self.declaredVars = dv
		self.sequence = Q
	def accept(self, visitor): visitor.visitBlock(self)
	def copy(self): return Block(self.declaredVars[:], self.sequence.copy())

class IfThenElse(Statement):
	def __init__(self, b, S1, S2):
		self.bool = b
		self.trueStatement = S1
		self.falseStatement = S2
	def accept(self, visitor): visitor.visitIfThenElse(self)
	def copy(self):
		return IfThenElse(
			self.bool.copy(),
			self.trueStatement.copy(),
			self.falseStatement.copy()
		)

class While(Statement):
	def __init__(self, b, S):
		self.bool = b
		self.bodyStatement = S
	def accept(self, visitor): visitor.visitWhile(self)
	def copy(self):
		return While(
			self.bool.copy(),
			self.bodyStatement.copy()
		)


class Declaration(Construct): pass

class VariableDeclaration(Declaration):
	def __init__(self, v):
		self.var = v
	def accept(self, visitor): visitor.visitVariableDeclaration(self)
	def copy(self): return VariableDeclaration(self.var.copy())

class MethodDeclaration(Declaration):
	def __init__(self, m, p, S):
		self.methodName = m
		if p: self.parameters = p
		else: self.parameters = []
		self.body = S
	def accept(self, visitor): visitor.visitMethodDeclaration(self)
	def copy(self):
		return MethodDeclaration(
			self.methodName.copy(),
			self.parameters[:],
			self.body.copy()
		)

class ConstructorDeclaration(Declaration):
	def __init__(self, p, S):
		if p: self.parameters = p
		else: self.parameters = []
		self.body = S
	def accept(self, visitor): visitor.visitConstructorDeclaration(self)
	def copy(self):
		return ConstructorDeclaration(
			self.parameters[:],
			self.body.copy()
		)

class ClassDeclaration(Declaration):
	def __init__(self, c, dv, ct, dm):
		self.className = c
		if dv: self.memberVars = dv
		else: self.memberVars = []
		self.constructor = ct
		if dm: self.methods = dm
		else: self.methods = []
	def accept(self, visitor): visitor.visitClassDeclaration(self)
	def copy(self):
		return ClassDeclaration(
			self.className.copy(),
			self.memberVars.copy(),
			self.constructor.copy(),
			self.methods[:]
		)


class Program(Construct):
	def __init__(self, dc, S):
		self.classDeclarations = dc
		self.initialStatement = S
	def accept(self, visitor): visitor.visitProgram(self)
	def copy(self):
		return Program(
			self.classDeclarations[:],
			self.initialStatement.copy()
		)


class ScopedStatement(Construct): pass

class BlockScopedStatement(ScopedStatement):
	def __init__(self, B):
		self.body = B
	def accept(self, visitor): visitor.visitBlockScopedStatement(self)
	def copy(self): return BlockScopedStatement(self.body.copy())

class MethodScopedStatement(ScopedStatement):
	def __init__(self, B):
		self.body = B
	def accept(self, visitor): visitor.visitMethodScopedStatement(self)
	def copy(self): return MethodScopedStatement(self.body.copy())
