#!/usr/bin/python

# TODO Later: Consider trying to pull out the "(%s)\s*" bits of tokenization
#             into an external module.

import re
import sys

import pdb

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

errPos = -1
errExpected = None

def parse_exact_str(s, code, pos):
  to_escape = list("+()")
  for e in to_escape: s = s.replace(e, "\\" + e)
  return parse_exact_re(s, code, pos)

def parse_exact_re(s, code, pos):
  #print("parse_exact(%s, <%s>)" % (s, code[pos:code.find('\n', pos)]))
  m = re.match(r"(%s)\s*" % s, code[pos:])
  #print("re=%s" % (r"(%s)\s*" % s))
  #print("m=%s" % `m`)
  if m: return m.group(1), pos + len(m.group(0))
  global errPos, errExpected
  if pos > errPos: errExpected, errPos = s, pos
  return None, pos

class SeqRule:
  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
    # TEMP
    if type(seq) is str:
      print("Error: SeqRule initated with string %s" % `seq`)
      print("Only compiled regex's and lists are expected")
      exit(1)
  def parse(self, code, pos):
    #if self.name == 'direct_assignment': pdb.set_trace()
    #print("parse <%s, %s>" % (self.name, code[pos:code.find('\n', pos)]))
    if type(self.seq) is not list:  # TEMP
      print("Error: Expected self.seq to be a list here")
      exit(1)
    pieces = {}
    startpos = pos
    for ruleName in self.seq:
      #print("Considering ruleName=%s" % ruleName)
      if ruleName[0] == "'": val, pos = parse_exact_str(ruleName[1:], code, pos)
      elif ruleName[0] == '"': val, pos = parse_exact_re(ruleName[1:-1], code, pos)
      else:
        val, pos = rules[ruleName].parse(code, pos)
        if val: pieces[ruleName] = pieces.get(ruleName, []) + [val[ruleName]]
      if val is None: return None, startpos
      #print("ruleName %s was found successfully" % ruleName)
    for key in pieces:
      if len(pieces[key]) == 1: pieces[key] = pieces[key][0]
    result = {self.name: (pieces if len(pieces) else val)}
    #if len(result) == 0: result[self.name] = val
    return result, pos
  def code(self, tree):
    # To set up:
    #   Any local keys as objects with a __str__ method and any given methods.
    #   A persistent compiler object
    #   An api object with methods: block, new_sym, err
    #   A self object with a str method/attribute.
    # Then:
    #   Execute the current object's code method.
    #
    # How to set up the node-based objects?
    # How to get self.str?
    #   Everything in a parse tree output could be a Rule Object, and this
    #   could already have the given methods associated with it.
    #   We could add a in_str property to replace self.str (it would be self.in_str).
    pass # TODO HERE


class OrRule:
  # Let's see if we can keep the or_list as a list of strings, and
  # do a dictionary lookup from that.
  def __init__(self, name, or_list):
    self.name = name
    self.or_list = or_list
  def parse(self, code, pos):
    #print("parse <%s, %s>" % (self.name, code[pos:code.find('\n', pos)]))
    # TODO Is there a better-fitting map-like function to do this?
    for r in self.or_list:
      #print("[[1]] %s" % r)
      val, pos = rules[r].parse(code, pos)
      #print("[[2]] val=%s" % `val`)
      if val:
        #print("Rule %s found successfully (as %s)" % (self.name, r))
        return {self.name: val}, pos
    return None, pos
  def code(self, tree): return rules[tree.keys()[0]].code(tree)

# TODO Does this need to be a Object object, or can
#      it just be object? Or is everything simpler if I
#      make my own Object superclass? (What is currently
#      called Object.)
rules = Object()

def parse_seq_str(seq_str):
  return [seq_str]
  if seq_str[0] == '"':
    return re.compile(r"(%s)\W+" % seq_str[1:-1])
  else:
    return None

def line_with_pos(code, pos):
  start = code.rfind('\n', 0, pos)
  if start == -1: start = 0
  end = code.find('\n', pos)
  #print("start=%d, end=%d" % (start, end))
  return code[start:end], pos - start

#rules.main = SeqRule(parse_seq_str('"abc"'))

ruleName = 'number'
rules[ruleName] = SeqRule(ruleName, parse_seq_str('"[0-9]+"'))

ruleName = 'identifier'
rules[ruleName] = SeqRule(ruleName, parse_seq_str(r'"[A-Za-z_]\w*"'))

# TODO add a function to parse a string into a list (or reuse parse_seq_str)
ruleName = 'direct_assignment'
rules[ruleName] = SeqRule(ruleName, ["identifier", "'=", "expression"])

ruleName = 'expression'
rules[ruleName] = OrRule(ruleName, ['identifier', 'number'])

ruleName = 'incremental_assignment'
rules[ruleName] = SeqRule(ruleName, ["identifier", "'+=", "expression"])

ruleName = 'assignment'
rules[ruleName] = OrRule(ruleName, ['direct_assignment', 'incremental_assignment'])

ruleName = 'print_statement'
rules[ruleName] = SeqRule(ruleName, ["'print", "identifier"])

ruleName = 'for_loop'
rules[ruleName] = SeqRule(ruleName, ["'for", "'(", "statement", "';", "conditional", "';", "statement", "')", "statement"])

ruleName = 'conditional'
rules[ruleName] = SeqRule(ruleName, ["expression", "'<", "expression"])

ruleName = 'statement'
rules[ruleName] = OrRule(ruleName, ['assignment', 'for_loop', 'print_statement'])

ruleName = 'main'
rules[ruleName] = OrRule(ruleName, ['statement'])

if len(sys.argv) < 2:
  print("Usage: %s <water-file>" % sys.argv[0])
  exit(2)
# TODO Clean up how I work with this file object.
code = open(sys.argv[1], 'r').read()

def run(tree):
  #print('run')
  print(tree)
  # TODO Uncomment these guys right heres.
  #code = rules.main.code(tree['main'])
  #print(code)

tree, pos = rules.main.parse(code, 0)
#print("tree=%s, pos=%s" % (`tree`, `pos`))
print("pos=%d" % pos)
#retval = rules.main.parse(code, 0)
#print('retval is %s' % `retval`)
#exit(0)
while tree:
  run(tree)
  tree, pos = rules.main.parse(code, pos)
  print("pos=%d" % pos)
  #print("tree=%s, pos=%s" % (`tree`, `pos`))
# TODO Later: Error recovery so we can provide
#   error messages beyond the first one.
# TODO Later: Track line numbers
if pos < len(code):
  print("Error: Expected %s at pos %d" % (errExpected, errPos))
  line, offset = line_with_pos(code, errPos)
  print(line)
  print(" " * offset + "^")
