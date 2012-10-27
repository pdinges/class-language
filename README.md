Interactive Interpreter for the Class Programming Language
==========================================================

The **Class** language is a (toy) [object-capability][objcap]
programming language.  It has formal semantics, which allows proving
that programs cannot violate the object-capability properties.  I
developed the language and its formal (operational) semantics as part
of [my master's thesis][class-thesis] as a (more) rigorous foundation
for research on object-capability programming languages.

Even though the development of **Class** focused on theoretical
studies, having an interpreter for the language was very helpful for
debugging the semantics.  This repository contains an interactive
interpreter for **Class** programs written in [Python2][python].  It
supports stepping through or executing programs, as well as inspecting
the resulting configurations.

I provide the interpreter here as an example for (a) how such an
interpreter can be implemented by hand, and (b) how to use
[PyMeta][pymeta] for parsing.  If you are developing a new programming
language, instead of writing everything by hand, consider using a
modern semantics framework like the [K framework][k] or
[Spoofax][spoofax].  Semantics defined in these frameworks are
executable, which means that they provide an interpreter for the
defined language *for free*.


System Requirements
-------------------

The interpreter is implemented in [Python][python], a dynamic
programming language available on all common platforms.  To be able to
run the interpreter, please install Python version 2.5 or greater on
your system.  Please refer to
[Python's own documentation][python-using] for instructions specific
to your platform.  Also, note that Python version 3.x is partially
incompatible with the 2.x series of Python.  The interpreter will
therefore *not* work with it.

Besides Python itself, the interpreter relies on the [PyMeta][pymeta]
module.  PyMeta is an object-oriented pattern matcher based on
[OMeta][ometa] and is used for parsing the **Class**-programs.  Please
ensure that it is available within Python's module path; you can
modify this path via the `PYTHONPATH` environment variable.  Again,
please refer to Python's documentation for exact instructions.  If
everything is set up correctly, Python's interactive command shell
allows importing the module via `import pymeta`.  Otherwise you will
receive an `ImportError` exception.


Installing and Running
----------------------

No installation is required for the **Class** interpreter---you can
start it directly from the downloaded repository.  Simply execute the
file `class_interpreter.py`.


Usage
-----

The interpreter provides an interactive shell for loading, executing
and inspecting **Class** programs; its prompt is the string `Class
Interpreter>`.  In the text below, `typewriter style` denotes
interaction with the interpreter.

Most of this section's documentation is available on line within the
interpreter.  You can use the command `help` to retrieve a list of
available commands.  To receive further information on a command *c*,
enter `help c`.  Issuing `exit` or `quit` will terminate the
interpreter.  An empty line repeats the previous command.

Note that you can speed up typing by using command and parameter
completion with the `Tab` key if the readline Python module is
installed.  Hitting the `Tab` key twice will present you with a list
of possible alternatives.  Readline comes as a part of Python itself
on Unix and related operating systems such as Linux and MacOS~X.


### Loading Programs

A typical session with the interpreter starts with loading a program
through the command `load`.

**Syntax:** `load <file name>`

The command loads and parses the program stored in file *<file name>*.
It returns nothing on success, but prints an error message if the file
could not be opened or the contents could not be parsed.

Please note that a limitation of the PyMeta pattern matcher reduces
the helpfulness of error messages.  The construct reported as causing
the error only marks the beginning of the *biggest* part that failed.
Hence, a whole construct, such as a class declaration, is tagged wrong
if one of its parts contains errors, for example if a method body
misses a semicolon.

**Example.** The interpreter comes together with an example program in
the file `busy.cls` that simulates the 3-state busy beaver.  We want
to experiment with it and therefore load it into the interpreter.
This results in below interaction.
~~~~
Class Interpreter> load busy.cls
Class Interpreter>
~~~~


### Executing and Stepping Through a Program

Loaded programs can be executed with the `step` command.  It applies
the transition relation *<number of steps>* times to the current
configuration.

**Syntax:** `step [<number of steps>]`

Note that it typically takes several applications of the transition
relation to execute a **Class** statement.  Therefore, *<number of
steps>* is always higher than the number of statements the program
advances.  If the number of steps is omitted, the program executes a
single step.

The command returns nothing on success and issues a note if the
program terminated.  The final store's contents will remain available
after the program finished.  However, the then-current frame contains
no variables and, hence, does not allow browsing through the store.
See the discussion on labelling objects for a workaround of this
limitation.

**Example.** Suppose we knew from previous experiments that it
requires 37 steps to execute all initialisation statements of the busy
beaver program.  Continuing above example, we fast forward to the
point where the `run()` method is called as shown below.
~~~~
Class Interpreter> step 37
Class Interpreter>
~~~~


### Printing the Current Configuration's Statement

How is it possible to know the number of steps it takes until a
certain statement?  A simple approach is to small-step through the
program and check the intermediate configurations' statements with the
`program` command.

**Syntax:** `program`

The command prints the statement of the current configuration.  The code
reflects all transformations that were applied during the execution up
to this point.

**Example.** Picking up the example again, we check whether 37 steps
really took us to the right statement in the program.
~~~~
Class Interpreter> program
[
  { self.run() };
  return self
]
Class Interpreter> 
~~~~

Note that the interpreter employs its own pretty printer to output the
statements.  Indentation and line-breaks will therefore possibly
differ from the source file's contents if you invoke the command
directly after loading a program.


### Inspecting the Store

Beside the current configuration's statement, it is also possible to
inspect its store.  The command `inspect` allows looking at objects.

**Syntax:** `inspect [--depth <depth>] <object path>+`

The optional parameter *<depth>* specifies the inspection depth *d*.
With *d=0*, only the specified object *obj* itself will be printed on
the screen.  A depth of *d>0* will treat all objects that *obj* holds
references to (in its member variables) as being specified, too, with
a depth of *d-1*.

A list of object paths specifies which objects to inspect.  An object
path is a, possibly empty, string that describes a reference to an
object in the store.  It consists of *segments* joined by periods.
For example, the object path `one.two` has two segments: `one` and
`two`.

Each segment names a member variable in the object designated by the
previous segment.  Their combination then stands for the reference
that is the value of this last member variable.  In above example,
path `one.two` denotes a reference to the object that member variable
`two` of (the object referred to by) `one` points to.

Object paths always start at the current frame object pointer.  Hence,
the path `one` means the reference that is the value of the current
frame's member variable `one`.  Because scoping requires indirection,
the object referred to is variable `one`'s *container*.  Consequently,
path `one.one` is the value of variable `one` in the current scope.
See the thesis section on memory contents in **Class** for a detailed
explanation.

Note that `Tab` completion also works for object paths: Pressing `Tab`
once completes the segment under the cursor as far as the current
prefix is unique; pressing it twice prints a list of valid
alternatives.

**Example.** After having seen the current configuration's statement
in the previous subsection, we have a look at some of the objects.  We
start by inspecting the current frame.
~~~~
Class Interpreter> inspect
================================
Object at ref:0x8a3e8cc
================================
char_0         ->  ref:0x8a3e06c
char_1         ->  ref:0x8a3e06c
current_state  ->  ref:0x8a3e06c
false          ->  ref:0x8a3e06c
head           ->  ref:0x8a3e06c
int:CLASS      ->  ref:0x882c28c
int:PREV       ->  ref:0x8a3e10c
self           ->  ref:0x8a3e14c
state_A        ->  ref:0x8a3e06c
state_B        ->  ref:0x8a3e06c
state_C        ->  ref:0x8a3e06c
true           ->  ref:0x8a3e06c
--------------------------------
--------------------------------

Class Interpreter> 
~~~~

Afterwards we check the cell under the Turing machine's read and write head.
~~~~
Class Interpreter> inspect head.head
==================================
Object at ref:0x8a3ec0c
==================================
content          ->  ref:0x8a3eb8c
default          ->  ref:0x8a3eb8c
left_neighbour   ->  ref:0x8a3ec0c
right_neighbour  ->  ref:0x8a3ec0c
----------------------------------
left()
read()
right()
set_left(l)
set_right(r)
write(c)
----------------------------------
Class Interpreter> 
~~~~

Internalised names are accessible through a special prefix to a
segment.  The segment `internal:class`, or `i:c` for short, denotes
the internalised name *class*.  Likewise, `internal:previous` or `i:p`
is the internalised name *prev*.

Two ways to describe absolute references complete above relative path
segments.  The first is by label via `label:foo` where `foo` was
assigned beforehand to an object path using the command `label`.
Prefix `l:` is an abbreviation for `label:`.  The second way is by
memory address using the prefix `reference:` or `r:`.

**Example.** The command `inspect i:prev.x.x` lets us look at the
object that is the value of variable `x` in the *previous* frame.


### Labelling Objects for Later Inspection

It is often convenient to remember objects for later inspection.  The
command `label` makes it possible to tag an object denoted by an
object path *<object path>* with a user-defined name *<name>*.  This
makes it easy to retrieve the object, even if it would be complicated
to address from within the current frame.

**Syntax:** `label <object path> <name>`

Afterwards, use the segment `label:<name>` to refer to the object.
This form will also be used as the preferred name when looking at
objects with `inspect`.

Set labels can be removed with the command `unlabel`.

**Syntax:** `unlabel <name>`

If an object path---even with a `label:` structure---is used as
argument instead of a simple name, all labels to the specified object
will be removed.

**Example.** Let us continue working with the busy beaver from the
previous example.  Our goal is to inspect the final tape contents.  A
possible approach is to remember the frame from the constructor and
check the bound variable `head` after the program terminated.  For
better readability, we also assign names to the tape symbols 0 and 1.
~~~~
Class Interpreter> label . cframe
Class Interpreter> label char_0.char_0 0
Class Interpreter> label char_1.char_1 1
Class Interpreter> step 500
The program finished execution after 386 steps.
Memory contents remain available for inspection
until a new program is loaded.
Class Interpreter> inspect l:cframe.head.head
==================================
Object at ref:0xa571e8c
==================================
content          ->  label:1
default          ->  label:0
left_neighbour   ->  ref:0xa56cc0c
right_neighbour  ->  ref:0xa5828ac
----------------------------------
left()
read()
right()
set_left(l)
set_right(r)
write(c)
----------------------------------
~~~~

From this cell on we can use the `left_neighbour` and
`right_neighbour` member variables to traverse the whole tape.


License
-------

Copyright (c) 2008--2012 Peter Dinges <pdinges@acm.org>.

The software in this repository is free software: you can redistribute
it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

The software is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the [GNU General Public License][gpl3]
along with this program.  If not, see <http://www.gnu.org/licenses/>.


[class-thesis]: http://www.elwedgo.de/fileadmin/elwedgo.de/portfolio/masters_thesis_cs/dinges-capability_language-thesis.pdf "Master's thesis: Structural Operational Semantics for an Idealised Object-Capability Programming Language"
[gpl3]: http://opensource.org/licenses/GPL-3.0 "GNU General Public License, version 3"
[k]: https://code.google.com/p/k-framework/ "K semantics framework"
[objcap]: http://en.wikipedia.org/wiki/Object-capability_model "Wikipedia article on object-capability security"
[ometa]: http://tinlizzie.org/ometa/ "OMeta parser combinator"
[pymeta]: https://launchpad.net/pymeta "Python implementation of OMeta"
[python]: http://python.org "Python programming language"
[python-using]: http://docs.python.org/using/ "Guide to installing and using Python"
[spoofax]: http://strategoxt.org/Spoofax "Spoofax semantics framework"
