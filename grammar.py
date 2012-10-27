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


from pymeta.grammar import OMeta
from constructs import *

# ===============
# Syntax of Class
# ===============
#
# See chapter 2 in the thesis for a BNF version of Class' syntax.  The syntax
# of OMeta is described in the paper "OMeta: an Object-Oriented Language
# for Pattern Matching" by Alessandro Warth and Ian Piumarta.  (Available
# from http://vpri.org/pdf/tr2007003_ometa.pdf )

__classGrammar = """
name	::= <spaces> <letter>:head <letterOrDigit>*:tail		=> Name(head + ''.join(tail))
names	::= <name>:head (<token ','> <name>)*:tail			=> [head] + tail
var	::= (<name>:x => x.name):y					=> Variable(y)
vars	::= <var>:head (<token ','> <var>)*:tail			=> [head] + tail

eq	::= <var>:y1 <token '='> <var>:y2				=> BoolEq(y1, y2)
neq	::= <var>:y1 <token '!='> <var>:y2				=> BoolNeq(y1, y2)
bool	::= <eq> | <neq>

varex	::= <var>:y							=> VarExpression(y)
new	::= <token 'new'> <name>:c <token '('> <vars>?:args <token ')'>	=> New(c, args)
call	::= <var>:y <token '.'> <name>:m <token '('> <vars>?:args <token ')'>	=> Call(y, m, args)
expr	::= <new> | <call> | <varex>

ass	::= <name>:x <token ':='> <expr>:e				=> Assign(x, e)
skip	::= <token 'skip'>						=> Skip()
return	::= <token 'return'> <var>:y					=> Return(y)
seq	::= <stmt>:head (<token ';'> <stmt>)*:tail			=> Sequence([head] + tail)
block	::= <token 'begin'> <decv>:dv <seq>:Q <token 'end'>		=> Block(dv, Q)
if	::= <token 'if'> <bool>:b <token 'then'> <stmt>:S1 <token 'else'> <stmt>:S2	=> IfThenElse(b, S1, S2)
while	::= <token 'while'> <bool>:b <token 'do'> <stmt>:S		=> While(b, S)
stmt	::= <ass> | <skip> | <return> | <block> | <if> | <while> | <expr>

decv	::= (<token 'var'> <name>:x <token ';'> => VariableDeclaration(x))*
decm	::= 	(
			<token 'method'> <name>:m
			<token '('> <names>?:params <token ')'>
			<token 'is'> <stmt>:S <token ';'>		=> MethodDeclaration(m, params, S)
		)*
decctor	::= <token 'constructor'>
		<token '('> <names>?:params <token ')'>
		<token 'is'> <stmt>:S <token ';'>			=> ConstructorDeclaration(params, S)
decc	::= 	(
		<token 'class'> <name>:c <token 'is'> <token 'begin'>
		<decv>:dv <decctor>:ct <decm>:dm
		<token 'end'> <token ';'>				=> ClassDeclaration(c, dv, ct, dm)
		)+

prog	::= <decc>:dc <new>:S						=> Program(dc, S)

bscope	::= <token '{'> <sstmt>:B <token '}'>				=> BlockScopedStatement(B)
mscope	::= <token '['> <sstmt>:B <token ']'>				=> MethodScopedStatement(B)
sass	::= <name>:x <token ':='> <mscope>:B				=> Assign(x, B)
sseq	::= (<bscope> | <mscope> | <sass>):head (<token ';'> <stmt>)+:tail	=> Sequence([head] + tail)
sstmt	::= <sseq> | <bscope> | <mscope> | <sass> | <stmt> | <seq>
"""

classGrammar = OMeta.makeGrammar(__classGrammar, globals(), name="Class")
