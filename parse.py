#!/usr/bin/python
#
# parse.py
#
# The code needed to build, modify, and run a dynamic language parser.
#
# TODO Document public functions.
#

import re


# Globals.

rules = None
modes = [{'id': '', 'opts': {}}]
mode = modes[-1]
parser = None

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
  def run_fn(self, fn_name, fn_code):
    local = {}
    exec fn_code in {}, local
    local[fn_name](self)
  def add_fn(self, fn_name, fn_code):
    fn_code = ('def %s(self):' % fn_name) + fn_code
    def run(self): self.run_fn(fn_name, fn_code)
    self[fn_name] = run

class SeqRule(Rule):
  def __init__(self, name, seq):
    self.name = name
    self.seq = seq
  def parse_mode(self):
    print('%s parse_mode' % self.name)
    init_num_modes = len(modes)
    if 'start' not in self.__dict__:
      fmt = 'Grammar error: expected rule %s to have a "start" method.'
      print(fmt % self.name)
      exit(1)
    self.start
    # TODO Handle a StopIteration exception here (it's a user error, but we
    #      should handle it gracefully).
    while len(modes) > init_num_modes: parser.next()
  def parse(self, code, pos):
    print('%s parse' % self.name)
    pieces = {}
    startpos = pos
    for rule_name in self.seq:
      print('rule_name=%s' % rule_name)
      if rule_name == '-|': return self.parse_mode()
      c = rule_name[0]
      if c == "'": val, pos = parse_exact_str(rule_name[1:], code, pos)
      elif c == '"': val, pos = parse_exact_re(rule_name[1:-1], code, pos)
      else:
        val, pos = rules[rule_name].parse(code, pos)
        if val: pieces[rule_name] = pieces.get(rule_name, []) + [val[rule_name]]
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

class FalseRule(Rule):
  def __init__(self, name):
    self.name = name
  def parse(self, code, pos):
    return None, pos

class ParseIterator(Object):
  def __init__(self, filename):
    f = open(filename)
    self.code = f.read()
    self.pos = 0
    f.close()
  def __iter__(self): return self
  def next(self):
    tree, self.pos = rules.phrase.parse(self.code, self.pos)
    if tree: return tree
    raise StopIteration
    

###############################################################################
#
# Public functions.
#
###############################################################################

def or_rule(name, or_list):
  rules[name] = OrRule(name, or_list)
  return rules[name]

def seq_rule(name, seq):
  rules[name] = SeqRule(name, seq)
  return rules[name]

def false_rule(name):
  rules[name] = FalseRule(name)
  return rules[name]

def file(filename):
  global parser
  parser = ParseIterator(filename)
  return parser

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

err_pos = -1
err_expected = None

def parse_exact_re(s, code, pos):
  m = re.match(r"(%s)\s*" % s, code[pos:])
  if m: return m.group(1), pos + len(m.group(0))
  global err_pos, err_expected
  if pos > err_pos: err_expected, err_pos = s, pos
  return None, pos

# TODO TEMP Goal: have rules[mode][rule_name] be the rule object, mode == ''
#                 means the global mode.
def get_base_rules():
  global rules
  rules = Object()

  # Global rules.
  or_rule('phrase', ['statement', 'comment', 'blank', 'grammar'])
  seq_rule('blank', [r'"\n"'])
  seq_rule('comment', [r'"#[^\n]*\n"'])
  false_rule('statement')
  or_rule('grammar', ['global_grammar', 'mode_grammar'])
  r = seq_rule('global_grammar', [r'">\n(?=(\s+))"', '-|'])
  #r.add_fn('start', " parse.push_mode('lang_def', {'indent': tokens[0][1]})")

  return rules

rules = get_base_rules()

