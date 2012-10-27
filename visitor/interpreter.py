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
from constructs import *
import pymeta.grammar
import util

# ================
# Semantic objects
# ================

class Reference(object):
	"""
	Identifiers for ClassObjects.
	"""
	pass

# The domain of object states are names; we represent them as strings.
# Consequently, object states in our interpreter are dictionaries mapping
# strings to References. Because integers always differ from strings, we
# use them as internalised names.

INAME = util.Enum(["PREV", "CLASS"])

# Similar to the object state, object behaviour maps (string) names to
# a tuple containing the implementation and argument mapping
# (see section 3.1.1).

class ClassObject(object):
	"""
	Objects of Class as introduced in section 3.1.
	"""
	def __init__(self, state = {}, behaviour = {}):
		self.__state = state
		self.__behaviour = behaviour
	
	def variable(self, x):
		return self.__state[x]
	
	def method(self, m):
		return self.__behaviour[m]
	
	def variables(self):
		return self.__state.keys()
	
	def references(self):
		return self.__state.values()
	
	def methods(self):
		return self.__behaviour.keys()
	
	def update(self, newState):
		self.__state.update(newState)
	
	def copy(self):
		return ClassObject(
			self.__state.copy(),
			self.__behaviour.copy()
		)


# Return values are the result of rule applications and, hence, appear in the
# abstract syntax tree.  We therefore add a special construct to represent
# them.
class ReturnValue(Construct):
	def __init__(self, ref):
		self.reference = ref




class InterpreterVisitor(Visitor):
	"""
	Applies the transition rules (section 3.3) to a tree of Constructs.
	
	The visitor encapsulates all program state outside the code.  It
	therefore contains the store and the frame object pointer.  Together
	with the code, this makes for a complete configuration (section 3.1.4).
	
	As the visitor traverses the tree, it applies the transition rules to
	the Constructs (modifying them!) and accordingly updates its store and
	frame object pointer.  With every application of the InterpreterVisitor
	to a Construct tree, the visitor executes one step of the respective
	program.
	"""
	
	def __init__(self, replaceRootConstruct):
		Visitor.__init__(self)
		self._store = {}
		self._fop = None
		
		self.__currentConstructAccessor = [ (replaceRootConstruct, None) ]


	# ===================
	# Auxiliary functions
	# ===================
	#
	# Section 3.2 of the thesis documents all auxiliary functions in detail
	# and context.  The functions are direct translations to Python with a
	# small exception: instead of returning a modified store, all
	# respective functions modify the passed store in place.  This saves us
	# the hassle of copying the store on each update.


	# Memory Management (see subsection 3.2.1 in the thesis).

	def _new(self, fop = None):
		"""
		Returns an unused reference.
		"""
		return Reference()

	def _put(self, obj):
		"""
		Saves the passed object in the store.
		"""
		ref = self._new(self._fop)
		self._store[ref] = obj
		return ref

	def _setv(self, state, ref):
		"""
		Partially updates the state of the object referred to.
		"""
		self._store[ref].update(state)


	# Variable Management (see subsection 3.2.2 in the thesis).
	
	def _declare(self, state, fop = None):
		"""
		Introduces temporary variables with given values in the frame.
		"""
		if not fop: fop = self._fop
		
		tmpp = self._put(ClassObject(state))
		self._setv( dict([ (x, tmpp) for x in state.keys() ]), fop )


	def _deref(self, x, fop = None):
		"""
		Resolves a variable's value in the frame.
		"""
		if not fop: fop = self._fop
		
		frameObj = None
		containerRef = None
		containerObj = None
		try:
			frameObj = self._store[fop]
			containerRef = frameObj.variable(x)
			containerObj = self._store[ containerRef ]
			return containerObj.variable(x)
		
		except KeyError:
			if frameObj and containerRef and containerObj:
				msg = "Containing object has no member variable '%s'?!" % x
			elif frameObj and containerRef:
				msg = "Containing object of '%s' does not exist." % x
			elif frameObj:
				msg = "Variable '%s' is undefined in the current frame." % x
			else:
				msg = "Frame object pointer is invalid."
			raise NameError(msg)


	# Stack and Frame Management (see subsection 3.2.3 in the thesis).
	
	def _framefrom(self, ref):
		"""
		Derives a frame from the object referred to.
		"""
		state = dict([ (x, ref) for x in self._store[ref].variables() ])
		state[INAME.PREV] = None
		state[INAME.CLASS] = self._store[self._fop].variable(INAME.CLASS)
		return ClassObject(state)


	def _push(self, obj):
		"""
		Makes the given object top of the stack.
		"""
		oldfop = self._fop
		self._fop = self._put(obj)
		self._setv( dict([ (INAME.PREV, oldfop) ]), self._fop )


	def _pop(self):
		"""
		Removes the topmost frame from the stack.
		"""
		self._fop = self._store[self._fop].variable(INAME.PREV)
		# Maybe call freeUnused() here.


	# Declaration Parsing (see subsection 3.2.4 in the thesis).
	
	def _pv(self, Dvs):
		"""
		Returns a mapping from variable names to nil.
		"""
		return dict([ (Dv.var.name, None) for Dv in Dvs ])
	
	def _pm(self, Dms):
		"""
		Returns an object behaviour constructed from the given list of
		method declarations.
		"""
		return dict([
			(	m.methodName.name,
				(m.body, [p.name for p in m.parameters]) )
			for m in Dms
		])
	
	def _pc(self, Dc):
		"""
		Parses class declarations into the format required for the
		initialisation in transition rule [prog].
		"""
		return (
			ClassObject( self._pv(Dc.memberVars), self._pm(Dc.methods) ),
			Dc.constructor.body,
			[p.name for p in Dc.constructor.parameters]
		)

	
	def _alloc(self):
		"""
		Returns the set of currently allocated and used references.
		"""
		usedReferences = set(self._fop)
		_collectReferences(self._fop, self._store, usedReferences)
		return usedReferences
	
	@staticmethod
	def _collectReferences(ref, sto, usedReferences, depth=-1):
		"""
		Recursively traverses the network of object references starting
		from the given point.  Visited references are collected in
		usedReferences.
		"""
		if not ref or depth == 0: return
		
		newReferences = set( sto[ref].references() ) - usedReferences
		usedReferences.update( newReferences )
		
		for r in newReferences:
			InterpreterVisitor._collectReferences(
				r,
				sto,
				usedReferences,
				depth - 1
			)

	
	def _freeUnused(self):
		"""
		Removes all unreachable, hence, unused objects from the store.
		"""
		for ref in set(self._store.keys()) - self._alloc():
			del self._store[ref]


	# ================
	# Transition rules
	# ================
	#
	# Each Construct in the syntax tree invokes the respective method of
	# this visitor when it accepts the visitor.  Because Constructs
	# represent entities of a syntactic category, below methods encapsulate
	# all transition rules that apply to that syntactic category.  See
	# section 3.3 in the thesis for a formal definition and explanation
	# of all transition rules.
	#
	# Note that the methods transform the tree they traverse.
	
	def visitVarExpression(self, varexpr):
		"""
		Transition rule [var].  See thesis for an explanation.
		"""
		self._push( self._store[self._fop].copy() )
		self.__replaceConstructWith(
			MethodScopedStatement( Return(varexpr.var) )
		)
	
	
	def visitCall(self, call):
		"""
		Transition rule [call].  See thesis for an explanation.
		"""
		targetReference =  self._deref(call.target.name)
		calledObject = self._store[ targetReference ]
			
		try:
			methodBody, argumentMapping = \
				calledObject.method(call.methodName.name)
		except KeyError:
			raise AttributeError(
				"Object '%s' has no method '%s'." %
				(call.target.name, call.methodName.name)
			)
		if len(argumentMapping) != len(call.arguments):
			raise IndexError(
				"Method '%s' of object '%s' takes exactly "
				"%i arguments; %i were given." %
				( call.methodName.name, call.target.name,
				len(argumentMapping), len(call.arguments) )
			)
		binding = dict([
				(argumentMapping[i], self._deref(call.arguments[i].name))
				for i in range(0, len(argumentMapping))
			])
		binding["self"] = targetReference
		self._push( self._framefrom(targetReference) )
		self._declare(binding)
		
		self.__replaceConstructWith(
			MethodScopedStatement(methodBody.copy())
		)
		

	def visitNew(self, new):
		"""
		Transition rule [new].  See thesis for an explanation.
		"""
		classRegistry = self._store[ self._store[self._fop].variable(INAME.CLASS) ]
		try:
			classObject = self._store[ classRegistry.variable(new.className.name) ]
		except KeyError:
			raise NameError("Cannot create undefined class '%s'." % new.className.name)
		
		objectPrototype = self._store[ classObject.variable("proto") ]
		newReference = self._put( objectPrototype.copy() )
		
		constructorBody, argumentMapping = classObject.method("ctor")
		if len(argumentMapping) != len(new.arguments):
			raise IndexError(
				"The constructor of class '%s' takes exactly "
				"%i arguments; %i were given." %
				(new.className.name, len(argumentMapping), len(new.arguments))
			)
		binding = dict([
				(argumentMapping[i], self._deref(new.arguments[i].name))
				for i in range(0, len(argumentMapping))
			])
				
		binding["self"] = newReference
			
		self._push( self._framefrom(newReference) )
		self._declare(binding)
		
		self.__replaceConstructWith(
			MethodScopedStatement( Sequence(
				[ constructorBody.copy(), Return( Variable("self") ) ]
			))
		)

	
	def visitAssign(self, ass):
		"""
		Transition rules [ass1], [ass2] and [ass3].  See thesis for
		an explanation.
		"""
		
		# [ass1]
		if isinstance(ass.rhs, Expression):
			self.__descendTo(ass, "rhs")
			
		elif isinstance(ass.rhs, ScopedStatement):
			self.__descendTo(ass.rhs, "body")
			
			# [ass3]
			if isinstance(ass.rhs.body, ReturnValue):
				self._pop()
				try:
					containerRef = self._store[ self._fop ].variable(ass.target.name)
				except KeyError:
					raise NameError(
						"Cannot assign to undefined variable '%s'." %
						ass.target.name
					)
				self._setv(
					dict([ (ass.target.name, ass.rhs.body.reference) ]),
					containerRef
				)
				self.__replaceConstructWith(None)
			
			# [ass2] is handled implicitly because it does not
			# change the tree any further.
	
	
	def visitSkip(self, skip):
		"""
		Transition rule [skip].  See thesis for an explanation.
		"""
		self.__replaceConstructWith(None)
	
	
	def visitReturn(self, ret):
		"""
		Transition rule [return].  See thesis for an explanation.
		"""
		self.__replaceConstructWith(
			ReturnValue( self._deref(ret.var.name) )
		)
	
	
	def visitBlock(self, block):
		"""
		Transition rule [block].  See thesis for an explanation.
		"""
		self._push( self._store[self._fop].copy() )
		self._declare( self._pv(block.declaredVars) )
		self.__replaceConstructWith(
			BlockScopedStatement(block.sequence)
		)
	
	
	def visitIfThenElse(self, ite):
		"""
		Transition rules [if1] and [if2].  See thesis for an explanation.
		"""
		
		# Evaluate booleans; this implements the semantic function B
		# from the thesis.
		ref1 = self._deref(ite.bool.var1.name)
		ref2 = self._deref(ite.bool.var2.name)

		if type(ite.bool) == BoolEq:
			b = (ref1 == ref2)
		elif type(ite.bool) == BoolNeq:
			b = (ref1 != ref2)
		
		if b:
			self.__replaceConstructWith( ite.trueStatement )
		else:
			self.__replaceConstructWith( ite.falseStatement )


	def visitWhile(self, whil):
		"""
		Transition rule [while].  See thesis for an explanation.
		"""
		self.__replaceConstructWith(
			IfThenElse(
				whil.bool,
				# Omit the block statement so we don't increase
				# the recursion depth. See visitSequence() for
				# respective flattening.
				Sequence([
					whil.bodyStatement.copy(),
					whil
				]),
				Skip()
			)
		)

	
	def visitSequence(self, seq):
		"""
		Transition rules [comp1], [comp2] and [comp3].  See thesis for
		an explanation.
		"""
		self.__descendTo(seq.statements, 0)
		if not seq.statements[0]: del seq.statements[0]
		
		# List is empty or a return value was generated.
		if not seq.statements:
			self.__replaceConstructWith(None)
		elif isinstance(seq.statements[0], ReturnValue):
			self.__replaceConstructWith(seq.statements[0])
		elif len(seq.statements) == 1:
			# Replace sequences of one element with the element.
			# This effectively flattens nested sequences resulting
			# from while statements.
			self.__replaceConstructWith(seq.statements[0])

	
	def visitBlockScopedStatement(self, B):
		"""
		Transition rules [subb1], [subb2] and [subb3].  See thesis for
		an explanation.
		"""
		self.__descendTo(B, "body")
		
		if not B.body or isinstance(B.body, ReturnValue):
			self._pop()
			self.__replaceConstructWith(B.body)

	
	def visitMethodScopedStatement(self, B):
		"""
		Transition rules [subc1], [subc2] and [subc3].  See thesis for
		an explanation.
		"""
		self.__descendTo(B, "body")
		
		if not B.body or isinstance(B.body, ReturnValue):
			self._pop()
			# Note that we always return None and terminate this
			# block (in contrast to visitBlockScopedStatement()).
			self.__replaceConstructWith(None)
	
	
	def visitProgram(self, prog):
		"""
		Transition rule [prog].  See thesis for an explanation.
		"""
		self._fop = self._put(ClassObject())
		self._setv( {INAME.PREV: self._fop}, self._fop )
		
		classRegistryState = {}
		for DecC in prog.classDeclarations:
			prototypeObject, constructorBody, argumentMapping = self._pc(DecC)
			protoReference = self._put(prototypeObject)
			
			classObject = ClassObject(
					{"proto": protoReference},
					{"ctor": (constructorBody, argumentMapping)}
				)
			classReference = self._put( classObject )
			
			classRegistryState[DecC.className.name] = classReference
		
		classRegistryReference = self._put( ClassObject(classRegistryState) )
		self._setv( {INAME.CLASS: classRegistryReference}, self._fop )
		
		self.__replaceConstructWith(prog.initialStatement)


	# =================
	# Utility functions
	# =================
	#
	# We need these functions to be able to transform the traversed tree
	# _in place_.  The problem is that Constructs don't know their parent
	# otherwise and thus could not replace themselves.
	
	def __descendTo(self, construct, key):
		"""
		Apply self to child 'key' of the given Construct and save this
		access path.  That way, nodes can replace themselves in the
		tree (using __replaceConstruct()).
		"""
		if type(construct) == list:
			self.__currentConstructAccessor.append(
				(construct.__setitem__, key)
			)
			construct.__getitem__(key).accept(self)
		elif isinstance(construct, Construct):
			self.__currentConstructAccessor.append(
				(construct.__setattr__, key)
			)
			construct.__getattribute__(key).accept(self)
		else:
			raise TypeError("Expected a Construct or a list of Constructs.")
		
		self.__currentConstructAccessor.pop()

	
	def __replaceConstructWith(self, construct):
		"""
		Replace the current node in the tree.  In order for this to
		work, the visitor must have traversed the tree using
		__descendTo().
		"""
		set, key = self.__currentConstructAccessor[-1]
		set(key, construct)



class InspectorInterpreterVisitor(InterpreterVisitor):
	"""
	Interprets a program represented by a tree of Constructs and allows
	access to runtime information for inspection and debugging.
	
	The class provides methods to conveniently access objects in the store
	through "object paths".  Objects may also be labelled for later
	inspection when their path changed.
	"""
	
	# Grammar to parse user input into the data structures expected by
	# the  methods label(), unlabel() and inspect().
	identifierGrammar = pymeta.grammar.OMeta.makeGrammar(
		"""
		name	::= <letterOrDigit>+:ls					=> "".join(ls)
		segment	::= (<name>:t ':' => t)?:typ <name>:val			=> (typ, val)
		frstseg	::= '.'? <segment> | ( '.' => (None, None) )
		objpath	::= <spaces> <frstseg>:head ('.' <segment>)*:tail '.'?	=> [head] + tail
		label	::= <spaces> <name>
		""",
		globals()
	)
	
	def __init__(self, replaceRootConstruct):
		InterpreterVisitor.__init__(self, replaceRootConstruct)
		
		self.__labels = {}
	
	
	def inspect(self, objectPath, depth=0):
		"""
		Get a list of object representations, starting from the given
		path up to the given depth.  The representation is intended
		for output to the user; all references are assigned
		human-readable names.
		
		The object path denotes a single object.  This, and all objects
		its member variables refer to (up to depth levels), will be
		included in the result.
		"""
		start = self.__lookup(objectPath)
		references = set([start])
		InterpreterVisitor._collectReferences(
			start, self._store, references, depth )
		
		objects = {}
		for ref in references:
			if not ref in self._store.iterkeys(): continue
			
			obj = self._store[ref]
			
			state = {}
			for var in obj.variables():
				# Translate internalised names to a human
				# readable form.
				name = {
					INAME.CLASS:"int:CLASS",
					INAME.PREV:"int:PREV"
				}.get(var, var)
				state[name] = self.__nameReference(obj.variable(var))
			
			beh = []
			for m in obj.methods():
				# The second item in method()'s result is the
				# list of parameters.
				beh.append( (m, obj.method(m)[1]) )
			
			objects[ self.__nameReference(ref) ] = (state, beh)
	
		return objects
	
	
	def label(self, objectPath, name):
		"""
		Assign an (absolute) label to the given object path.  The label
		can be used to later on refer to an object from the current
		(relative) context.
		"""
		self.__labels[name] = self.__lookup(objectPath)
	
	
	def unlabel(self, name):
		"""
		Remove a label.  If the given name is a valid label, it will be
		deleted.  Otherwise, it will be interpreted as object path and
		all labels denoting the resolved reference will be removed.
		"""
		if name in self.__labels.iterkeys():
			del self.__labels[name]
			return
		try:
			if not type(name) == list: return
			
			ref = self.__lookup(name)
			if ref in self.__labels.itervalues():
				# Avoid mutating iterated lists.
				delList = [
					k
					for k,v in self.__labels.iteritems()
					if v == ref
				]
				for k in delList: del self.__labels[k]
		except:
			# We tried to do something useful with the name and
			# failed.  Now let's simply get over with it.
			pass
	
	
	def labels(self):
		"""
		Currently declared labels.
		"""
		return self.__labels.keys()
	
	
	def __nameReference(self, ref):
		"""
		Find best absolute object path for the given reference.  This
		path doubles as the reference's "name" (for the user).
		"""
		if not ref in self._store.iterkeys():
			return "NIL"
		
		labels = [
			"label:%s" % l
			for l, r in self.__labels.iteritems() if r == ref
		]
		if labels:
			return ", ".join(labels)
		else:
			return "ref:0x%x" % id(ref)
	
	
	def __lookup(self, objectPath):
		"""
		Retrieve the reference described by objectPath.
		
		See above grammar and  ClassInterpreterCmd.help_objpath() for
		a syntax description of object paths.  This method expects
		the path to be parsed already.
		"""
		ref = self._fop
		
		for typ, val in objectPath:
			if not val: continue
			
			if typ:
				# Internalised names
				if typ.lower() in [ "i", "int", "internal" ]:
					if val.lower() in [ "c", "cls", "class" ]:
						val = INAME.CLASS
					elif val.lower() in [ "p", "prev", "previous" ]:
						val = INAME.PREV
					else:
						raise KeyError("Unknown internalised name '%s'." % val)
				
				# Labeled objects
				elif typ.lower() in [ "l", "label" ]:
					if self.__labels.has_key(val):
						ref = self.__labels[val]
						continue
					else:
						raise KeyError("Label '%s' does not exist." % val)
				
				# Memory addresses
				elif typ.lower() in [ "r", "ref", "reference" ]:
					# Note: This might raise ValueErrors.
					# Hexadecimal addresses have prefix "0x";
					if val.lower().startswith("0x"):
						addr = int(val[2:], 16)
					# Everything else is decimal.
					else:
						addr = int(val)
					
					# There should be exactly one object in
					# the store that has the given address.
					refs = [ r for r in self._store.keys() if id(r) == addr ]
					if not refs:
						raise KeyError("Found no reference with address '%s'." % val)
					ref = refs[0]
					continue
				
				else:
					raise KeyError("Unknown prefix '%s'." % typ)
		
			if not self._store.has_key(ref):
				raise KeyError("There is no object at "
					"reference '%s' (anymore?)." %
					self.__nameReference(ref))
			obj = self._store[ref]
			
			if not val in obj.variables():
				raise KeyError("The object at reference '%s' "
					"has no member variable '%s'." %
					(self.__nameReference(ref), val))
			
			ref = obj.variable(val)
		
		return ref
