#!/usr/bin/env python

# $Id$

# Python built-in modules
import cmd
import codecs
import locale
import os
import os.path
import sys
import textwrap
import traceback

# PyMeta parser framework
import pymeta.runtime

# Class
from grammar import classGrammar
from visitor.pprinter import PrettyPrintVisitor
from visitor.interpreter import InspectorInterpreterVisitor


class ClassInterpreterCmd(cmd.Cmd):
	"""
	Interactive shell for interpreting Class programs.
	"""
	
	# Grammar for parsing arguments.  It uses the InspectorInterpreterVisitor's
	# grammar that explains the structure of identifiers such as object paths.
	_argsGrammar = InspectorInterpreterVisitor.identifierGrammar.makeGrammar(
		"""
		reqspace		::= <anything>:x ?( x.isspace() )
		reqspaces		::= <reqspace> <spaces>
		posint			::= <spaces> <digit>+:ds		=> int("".join(ds))
		switch :short :long	::= '-' '-' <token long> | '-' <token short>
		
		stepArgs		::= <posint>?
		labelArgs		::= <objpath>:path <reqspaces> <label>:label	=> (path, label)
		unlabelArgs		::= <objpath>
		depthSwitch		::= <switch 'd' 'depth'> <posint>:d <reqspaces>	=> d
		pathList		::= <objpath>:phead (<reqspaces> <objpath>)*:ptail	=> [phead] + ptail
		inspectArgs		::= <depthSwitch>?:depth <pathList>:paths => (paths, depth)
		""",
		globals()
	)

	
	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = "Class Interpreter> "
		self._AST = None
		self._interpreter = None
		self.__outputBuffer = []
		
		try:
			import readline
			# Having the period as delimiter interferes a bit with
			# filename completion.  It is, however, more important
			# to get correct object path completion.
			readline.set_completer_delims("\n\t .\\/")
		except ImportError:
			pass


	# ====================
	# Interpreter Commands
	# ====================

	def do_load(self, args):
		"""
		Load and parse Class programs.
		
		This method does input sanitation only; method _load() performs
		the actual work.
		"""
		if not args.strip():
			self._help_loadSyntax()
			return
		
		try:
			fileName = args.split()[0]
			file = codecs.open(fileName, "r", locale.getpreferredencoding())
			self._load(file)
		
		except IOError, e:
			self._printError(
				"Could not open file '%s'. %s." % (fileName, e.args[1])
			)
	
	
	def do_program(self, args):
		"""
		Pretty print current configuration's program.
		"""
		if not self._AST:
			self._printWarning(
				"Please load a program first (using 'load')."
			)
			return
		
		ppv = PrettyPrintVisitor()
		self._AST.accept(ppv)
		self.stdout.write( "\n%s\n" % ppv )


	def do_step(self, args):
		"""
		Execute one or more steps of the currently loaded program.
		
		This method does input sanitation only; method _step() performs
		the actual work.
		"""
		if not self._AST:
			self._printWarning(
				"Please load a program first (using 'load')."
			)
			return
		
		try:
			steps = self.__parseArgs(args, "stepArgs")
			if not steps: steps = 1
			
			self._step(steps)
		
		except ValueError:
			self._help_stepSyntax()


	def do_inspect(self, args):
		"""
		Inspect objects in the store.
		
		This method does input sanitation only; method _inspect()
		performs the actual work.
		"""
		if not self._interpreter:
			self._printWarning(
				"Program execution has not started, yet---the "
				"memory is empty. Please use the 'step' command "
				"to execute the program."
			)
			return
		
		# Default to current frame object.
		if not args.strip(): args = "."
		
		try:
			paths, depth = self.__parseArgs(args, "inspectArgs")
			self._inspect(paths, depth)
		
		except ValueError:
			self._help_inspectSyntax()
	
	
	def do_label(self, args):
		"""
		Assign a label to an object path.
		"""
		if not self._interpreter:
			self._printWarning(
				"Program execution has not started, yet---the "
				"memory is empty. Please use the 'step' command "
				"to execute the program."
			)
			return
		
		try:
			objectPath, label = self.__parseArgs(args, "labelArgs")
			self._interpreter.label(objectPath, label)
		
		except ValueError:
			self._help_labelSyntax()
	
	
	def do_unlabel(self, args):
		"""
		Remove a label, or all labels for an object path.
		"""
		try:
			path = self.__parseArgs(args, "unlabelArgs")
			# Label names look like object path segments.
			# If the path has length 1, the user probably
			# meant a label.
			if len(path) == 1 \
				and not path[0][0] \
				and path[0][1] in self._interpreter.labels():
				self._interpreter.unlabel(path[0][1])
			else:
				self._interpreter.unlabel(path)
		
		except ValueError:
			self._help_unlabelSyntax()

	
	def do_EOF(self, args):
		"""
		Exit interpreter shell.  See do_exit().
		"""
		print
		return self.do_exit(args)

	
	def do_quit(self, args):
		"""
		Exit interpreter shell.  See do_exit().
		"""
		return self.do_exit(args)
		
	
	def do_exit(self, args):
		"""
		Exit interpreter shell.
		"""
		try:
			answer = raw_input(
				"WARNING: Really exit Class Interpreter? "
				"Anything except 'y' or 'yes' means no. Answer: "
			)
			if answer.lower() in ["y", "yes"]:
				return True
			else:
				return False
		
		except EOFError:
			return False

	
	# =======================
	# Command Implementations
	# =======================
	
	def _load(self, file):
		"""
		Load and parse a program from the given file object.
		"""
		try:
			sourceCode = file.read().expandtabs()
			
			parser = classGrammar(sourceCode)
			self._AST = parser.apply("prog")
			self._interpreter = None
		
		except pymeta.runtime.ParseError:
			pos = parser.input.position
			lineStart = sourceCode.rfind("\n", 0, pos) + 1
			lineText = sourceCode[lineStart:].splitlines()[0]
			lineNr = max(len( sourceCode[:pos].splitlines() ), 1)
			columnNr = pos - lineStart + 1
			
			self._printError(
				"Error parsing line %i, character %i:" %
				(lineNr, columnNr)
			)
			self._print( ">>> %s" % lineText )
			self._print( "    %s" % ((columnNr - 1) * " " + "^") )
	
	
	def _step(self, steps=1):
		"""
		Execute the currently loaded program one or more steps.
		"""
		if not self._interpreter:
			# self.__replaceAsRoot is the callback function for the
			# visitor that it to replace the AST's root node.
			self._interpreter = InspectorInterpreterVisitor(
				self.__replaceAstRoot
			)
		
		try:
			for i in range(0, steps):
				if not self._AST:
					self._finished(i)
					return
				self._AST.accept(self._interpreter)
			
			if not self._AST:
				self._finished()
		
		except AttributeError, e:
			self._printError(
				"A runtime error occured in step number %i."
			)
			self._print(">>> %s" % ((i+1), e.message))
		except LookupError, e:
			self._printError(
				"A runtime error occured in step number %i."
			)
			self._print(">>> %s" % ((i+1), e.message))
		except NameError, e:
			self._printError(
				"A runtime error occured in step number %i."
			)
			self._print(">>> %s" % ((i+1), e.message))

	
	def _inspect(self, paths, depth=0):
		"""
		Print objects from the store.
		"""
		if not depth: depth=0
		
		errors = []
		objects = {}
		for path in paths:
			try:
				objects.update(
					self._interpreter.inspect(path, depth)
				)

			except KeyError, e:
				errors.append(e.message)
			except ValueError,e :
				errors.append(e.message)
		
		for name, obj in objects.iteritems():
			print ClassInterpreterCmd._formatInspectedObject(name, obj)
			print

		if errors:
			self._printWarning("Some errors occured.")
			for msg in errors:
				self._print( ">>> %s" % msg )
	
	
	def _finished(self, step=0):
		"""
		Notify the user that the program finished execution.
		"""
		if step > 1:
			msg = "The program finished execution after %i steps." % (step+1)
		else:
			msg = "The program finished execution."
			
		self._print(
			msg +
			" Memory contents are available for inspection until "
			"a new program is loaded."
		)
	
	
	# ==================
	# Command Completion
	# ==================

	def complete_load(self, text, line, begidx, endidx):
		# Complete first argument only.
		tokens = line.split()
		if len(tokens) > 2: return
		if len(tokens) == 2 and begidx == endidx: return
		if len(tokens) == 1: tokens.append("")
		
		path, file = os.path.split(tokens[1])
		if not path: path = "."
		
		matches = [ f for f in os.listdir(path) if f.startswith(text) ]
		for i in range(0, len(matches)):
			f = os.path.join(path, matches[i])
			# Append slash to directories so that completion
			# continues directly.
			if os.path.isdir(f):
				matches[i] += "/"
			elif os.path.isfile(f):
				matches[i] += " "
		if len(matches) > 1 or \
			(len(matches) == 1 and matches[0] != text):
				return matches

	
	def complete_inspect(self, text, line, begidx, endidx):
		return self.__completeObjPath(text, line, begidx, endidx)
	
	
	def complete_label(self, text, line, begidx, endidx):
		if len(line.split()) > 2:
			return []
		elif len(line.split()) == 2 and line[endidx - 1].isspace():
			return []
		
		return self.__completeObjPath(text, line, begidx, endidx)
	
	
	def complete_unlabel(self, text, line, begidx, endidx):
		candidates = []
		
		try:
			candidates.extend([
				"%s " % l for
				l in self._interpreter.labels()
				if l.startswith(text)
			])
			
			if not candidates:
				candidates.extend(
					self.__completeObjPath(text, line, begidx, endidx)
				)
		
		except Exception, e:
			print "Exception", e
		
		return candidates
	
	
	def __completeObjPath(self, text, line, begidx, endidx):
		"""
		Generic method for completing object paths.  It only ensures
		input validity and parses the path.  For actual completion
		see method __completeLastSegment().
		"""
		pathBegidx = begidx
		while pathBegidx > 0 and not line[pathBegidx - 1].isspace():
			pathBegidx -= 1
	
		try:
			pathPrefix = line[ pathBegidx : begidx ]
			if not pathPrefix:
				pathPrefix = "."
			
			path = self.__parseArgs( pathPrefix, "objpath"  )
			return self.__completeLastSegment(path, text)

		except ValueError:
			self.__outputBuffer = []

		

	def __completeLastSegment(self, path, segment):
		"""
		Return a list of candidates matching the given segment on the
		given object path.
		"""
		candidates = []
		
		if ":" in segment:
			typ, name = segment.split(":")
			
			if typ.lower() in [ "l", "label" ]:
				for label in self._interpreter.labels():
					if label.startswith(name):
						candidates.append( "%s:%s." % (typ, label) )
			
			elif typ.lower() in [ "i", "int", "internal" ]:
				for iname in [ "CLASS", "PREVIOUS" ]:
					if iname.startswith(name.upper()):
						candidates.append( "%s:%s." % (typ, iname) )
		
		else:
			if path == [(None, None)]:
				for prefix in [ "internal:", "reference:", "label:" ]:
					if prefix.startswith(segment):
						candidates.append(prefix)
			
			try:
				name, (state, beh) = self._interpreter.inspect(path).items()[0]
				for var, ref in state.iteritems():
					if var.startswith(segment):
						if ref == "NIL":
							candidates.append("%s " % var)
						else:
							candidates.append("%s." % var)
			except:
				pass
	
		return candidates

	
	# ====
	# Help
	# ====

	def _help_loadSyntax(self):
		self._print(
			"SYNTAX:    load <file name>"
		)

	def help_load(self):
		self._help_loadSyntax()
		self._print()
		self._print(
			"Loads and parses the Class program stored in "
			"file <file name>. Use the 'step' command to start "
			"execution."
		)
	
	
	def _help_programSyntax(self):
		self._print(
			"SYNTAX:    program"
		)

	def help_program(self):
		self._help_programSyntax()
		self._print()
		self._print(
			"Prints the program code for the current configuration. "
			"The code reflects all transformations that were "
			"applied during the execution up to this point."
		)
	
	
	def _help_stepSyntax(self):
		self._print(
			"SYNTAX:    step [<number of steps>]"
		)
	
	def help_step(self):
		self._help_stepSyntax()
		self._print()
		self._print(
			"Executes <number of steps> steps of the loaded program. "
			"If the argument is omitted, the program is advanced "
			"one step."
		)
		
	
	def help_objectpath(self):
		self._print(
			"An object path is a possibly empty string that "
			"describes a reference to an object in the store. It"
			"consists of segments joined by periods. For example, "
			"the object path 'one.two.three' has three segments: "
			"'one', 'two' and 'three'."
		)
		self._print()
		self._print(
			"Each segment names a member variable in the object "
			"designated by the previous segment. Their combination "
			"then stands for the reference that is the value of "
			"this last member variable. In above example, 'one.two' "
			"is a reference to the object that member variable "
			"'two' of (the object referred to by) 'one' points to."
		)
		self._print()
		self._print(
			"Object paths always start at the current frame object "
			"pointer. Hence, the path 'one' is the reference that "
			"is the value of the current frame's member variable "
			"'one'. Because frames model scopes, the referred "
			"object is variable 'one''s _container_. Consequently, "
			"path 'one.one' is the value of variable 'one' in the "
			"current scope."
		)
		self._print()
		self._print(
			"Internalised names may be accessed through a special "
			"prefix to a segment. The segmet 'internal:class', or "
			"'i:c' for short, denotes the internalised name "
			"'class'. Likewise, 'internal:previous' or 'i:p' is "
			"the internalised name 'prev'."
		)
		self._print()
		self._print(
			"Complementing above relative path segments are two "
			"ways to describe absolute references. The first is by "
			"label via 'label:foo' where 'foo' was assigned "
			"beforehand to an object path using the command 'label'. "
			"Prefix 'l:' is an abbreviation for 'label:'."
		)
		self._print()
		self._print(
			"The second way is by memory address using the prefix "
			"'reference:' or 'r:'."
		)
	
	
	def _help_inspectSyntax(self):
		self._print(
			"SYNTAX:    inspect [--depth <depth>] [<object path>]*"
		)
	
	def help_inspect(self):
		self._help_inspectSyntax()
		self._print()
		self._print(
			"Print objects from the current configuration's store."
		)
		self._print()
		self._print(
			"The optional parameter '--depth' (or '-d', for short) "
			"specifies the inspection depth d.  Having d=0 means "
			"that only the specified object X will be printed. A "
			"depth of d>0 will treat all objects that X holds "
			"references to (in its member variables) as being "
			"specified, too, with a depth of d-1."
		)
		self._print()
		self._print(
			"Object paths specifiy which objects to inspect; see "
			"'help objectpath' for an explanation. If no path was "
			"given, the current configuration's frame will be "
			"printed."
		)
	
	
	def _help_labelSyntax(self):
		self._print(
			"SYNTAX:    label <objectPath> <name>"
		)
		
	def help_label(self):
		self._help_labelSyntax()
		self._print()
		self._print(
			"Assigns an (absolute) label <name> to an object "
			"described by a (relative) object path <object path>. "
			"The label can be used to later on refer to the object "
			"even if its path changed by employing the object path "
			"'label:<name>'. The label will also be used as the"
			"preferred name when inspecting the object using the "
			"command 'inspect'."
		)
		self._print()
		self._print(
			"See 'help objectpath' for an explanation of how "
			"to specify objects with object paths."
		)
	
	
	def _help_unlabelSyntax(self):
		self._print(
			"SYNTAX:    unlabel (<label> | <objectPath>)"
		)
	
	def help_unlabel(self):
		self._help_unlabelSyntax()
		self._print()
		self._print(
			"Removes a label given to an object through the "
			"'label' command."
		)
		self._print()
		self._print(
			"To remove all labels given to a specific object, it "
			"is also possible to pass an object path as argument "
			"(even one with a 'label:' structure). See 'help "
			"objectpath' for an explanation on object paths."
		)
	
	
	def help_exit(self):
		self._print(
			"SYNTAX:    exit"
		)
		self._print()
		self._print(
			"Exits the program."
		)
		
	def help_quit(self):
		self.help_exit()
	
	
	# =================
	# Utility Functions
	# =================

	def __replaceAstRoot(self, key, value):
		"""
		Provided to the InterpreterVisitor to allow it replacing the
		AST's root node.
		"""
		self._AST = value


	def __parseArgs(self, args, rule):
		"""
		Generic parsing function that applies a rule of _argsGrammar to
		command arguments.
		"""
		try:
			uargs = unicode(args, locale.getpreferredencoding()).strip()
			parser = self._argsGrammar(uargs)
			ret = parser.apply(rule)
			pos = parser.input.position
			if not pos == len(uargs):
				self._printWarning(
					"Ignored leftover arguments '%s'" % uargs[pos:].strip()
				)
			return ret
		
		except pymeta.runtime.ParseError:
			pos = parser.input.position
			self._printError("Could not parse arguments.")
			self._print(">>> %s" % uargs)
			self._print("    %s" % ((pos * " ") + "^"))
			raise ValueError()
	
	
	
	# ======
	# Output
	# ======

	def postcmd(self, stop, line):
		"""
		Print the output buffer after the command finished execution.
		"""
		if self.__outputBuffer:
			e = locale.getpreferredencoding()
			wrapper = textwrap.TextWrapper()
			lines = [ wrapper.fill(l.encode(e)) for l in self.__outputBuffer ]
			self.stdout.write(
				"\n%s\n\n" % ("\n".join(lines))
			)
		
		self.__outputBuffer = []
		return stop
	
	
	def _print(self, text=""):
		self.__outputBuffer.append(text)
	
	
	def _printWarning(self, text):
		self.__outputBuffer.append("WARNING: %s" % text)
	
	
	def _printError(self, text):
		self.__outputBuffer.append("ERROR: %s" % text)
	
	
	
	@staticmethod
	def _formatInspectedObject(name, obj):
		"""
		Pretty print objects received from the
		InspectorInterpreterVisitor's inspect() method.
		"""
		state, beh = obj

		text = [
			"=",
			"Object at %s" % name,
			"="
		]
	
		# Align member variable values by printing all names in the
		# same (maximal) width (using ljust()).
		# Note: Argument to max() must not be the empty list.
		width = max( [ len(key) for key in state.iterkeys() ] + [0])
		varNames = state.keys()
		varNames.sort()
		for key in varNames:
			text.append( "%s  ->  %s" % (key.ljust(width), state[key]) )
		text.append("-")
		
		beh.sort()
		for meth, params in beh:
			text.append( "%s(%s)" % (meth, ", ".join(params)) )
		text.append("-")
		
		# Expand separator place holders to maximum line width.
		width = max( [ len(line) for line in text ] )
		for i in range(0, len(text)):
			if text[i] in [ "=", "-" ]:
				text[i] = width * text[i]

		# Python automatically translates this to the correct platform
		# newline sequence.
		return "\n".join(text)


if __name__ == "__main__":
	# Switch to the locale prefered by the user
	locale.setlocale(locale.LC_ALL, '')
	ClassInterpreterCmd().cmdloop()
