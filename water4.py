#!/usr/bin/python
#
# water4.py
#
# Goal: Improving from water3, be able to read in a language definition file
#       and then parse another file written in that language. Also, to do so
#       in a way that includes source-to-output translation rules, and doesn't
#       just produce a parse tree.
#       
# In particular, take two steps in writing this file:
# 1. Get read_lang_def to parse and understand language definition2.water.
# 2. Use the output of 1 to parse the statements at the bottom of that file.
#
# Future steps:
# 3. Actually execute sample1.water.
# 4. Begin work to unify how these two files are read in, so that they are no
#    longer separate steps.
#

import re
import sys

###############################################################################
#
# Define classes.
#
###############################################################################

class Object(object):
  # Enable parentheses-free method calls, as in: retVal = myObj.method
  def __getattribute__(self, name):
    val = object.__getattribute__(self, name)
    try: return val()
    except: return val
  # Enable bracket-syntax on attributes, as in: retVal = myObj[methodName]
  def __getitem__(self, name): return self.__getattribute__(name)
  def __setitem__(self, name, value): self.__dict__[name] = value

class Rule(Object):
  pass

class SeqRule(Rule):
  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
  def parse(self, code, pos):
    pieces = {}
    startpos = pos
    for ruleName in self.seq:
      if ruleName[0] == "'": val, pos = parse_exact_str(ruleName[1:], code, pos)
      elif ruleName[0] == '"': val, pos = parse_exact_re(ruleName[1:-1], code, pos)
      else:
        val, pos = rules[ruleName].parse(code, pos)
        if val: pieces[ruleName] = pieces.get(ruleName, []) + [val[ruleName]]
      if val is None: return None, startpos
    for key in pieces:
      if len(pieces[key]) == 1: pieces[key] = pieces[key][0]
    result = {self.name: (pieces if len(pieces) else val)}
    return result, pos

class OrRule(Rule):
  def __init__(self, name, or_list):
    self.name = name
    self.or_list = or_list
  def parse(self, code, pos):
    for r in self.or_list:
      val, pos = rules[r].parse(code, pos)
      if val: return {self.name: val}, pos
    return None, pos

###############################################################################
#
# Define functions.
#
###############################################################################

def parse_exact_str(s, code, pos):
  to_escape = list("+()")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return parse_exact_re(s, code, pos)

# TODO Consider ways to do this witout using globals.

errPos = -1
errExpected = None

def parse_exact_re(s, code, pos):
  m = re.match(r"(%s)\s*" % s, code[pos:])
  if m: return m.group(1), pos + len(m.group(0))
  global errPos, errExpected
  if pos > errPos: errExpected, errPos = s, pos
  return None, pos


###############################################################################
#
# Medium-level code.
#
# These are any functions called directly by any high-level code.
#
###############################################################################

def get_base_rules():
  rules = Object()
  rules.phrase = SeqRule('phrase', ["'hi", "'there"])
  return rules

###############################################################################
#
# Begin high-level goal code.
#
###############################################################################

def exec_file(filename):
  f = open(filename)
  code = f.read()
  f.close()
  rules = get_base_rules()
  tree, pos = rules.phrase.parse(code, 0)
  while tree:
    print(tree)
    tree, pos = rules.phrase.parse(code, pos)


if __name__ == '__main__':
  exec_file('language definition2.water')

